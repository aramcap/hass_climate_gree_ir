#!/usr/bin/env python3
"""
Generador de payloads IR para aire acondicionado Gree/Daitsu.
Genera comandos compatibles con Broadlink RM4C Mini.

Uso:
    python3 gree_ir_generator.py --mode heat --temp 22 --power on
    python3 gree_ir_generator.py --mode cool --temp 26 --power on --fan high
    python3 gree_ir_generator.py --power off
    python3 gree_ir_generator.py --mode heat --temp 21 --power on --output raw
"""

import argparse
import base64
import sys

# Mapeo de modos HVAC
GREE_MODES = {
    "auto": 0x00,
    "cool": 0x01,
    "dry": 0x02,
    "fan_only": 0x03,
    "heat": 0x04,
}

# Mapeo de velocidades de ventilador
GREE_FAN_MODES = {
    "auto": 0b00,
    "high": 0b11,
    "medium": 0b10,
    "low": 0b01,
}

# Constantes de timing IR (valores RAW para Broadlink)
HDR_MARK = 0x011F   # ~8740µs
HDR_SPACE = 0x90    # ~4385µs
BIT_MARK = 20       # ~610µs
ZERO_SPACE = 18     # ~548µs
ONE_SPACE = 54      # ~1644µs
FOOTER = 19         # ~579µs (byte final de frame)
GAP = 0x81          # ~3928µs (separación entre frames)


def build_gree_command(hvac_mode: str, temp: int, power: bool, fan_mode: str = "auto") -> bytes:
    """
    Construye los 4 bytes del comando Gree.
    
    Estructura:
        Byte 0: mode(3 bits) | power(1 bit) | fan(2 bits)
        Byte 1: temperatura - 16
        Byte 2: 0x60 (ON) o 0x20 (OFF)
        Byte 3: 0x50 (constante)
    
    Args:
        hvac_mode: Modo de operación (auto, cool, dry, fan_only, heat)
        temp: Temperatura objetivo (16-30)
        power: True para encender, False para apagar
        fan_mode: Velocidad del ventilador (auto, high, medium, low)
    
    Returns:
        4 bytes del comando Gree
    """
    mode_bits = GREE_MODES.get(hvac_mode, 0x01)
    fan_bits = GREE_FAN_MODES.get(fan_mode, 0b00)
    power_bit = 1 if power else 0
    
    byte0 = (mode_bits & 0x07) | (power_bit << 3) | ((fan_bits & 0x03) << 4)
    byte1 = max(0, min(14, temp - 16))
    byte2 = 0x60 if power else 0x20
    byte3 = 0x50
    
    return bytes([byte0, byte1, byte2, byte3])


def encode_ir_packet(gree_bytes: bytes) -> bytes:
    """
    Codifica los bytes Gree en un paquete IR completo para Broadlink.
    
    Estructura del paquete:
        - Header: 0x26 0x00 + longitud (2 bytes little-endian)
        - Frame 1: Header IR + 32 bits (4 bytes LSB-first) + conector (010) + footer
        - Frame break: 0x00 0x02 0x81
        - Frame 2: 28 bits cero + 4 bits checksum + 1 bit cero + footer
        - End markers: 0x0D 0x05
    
    Args:
        gree_bytes: Los 4 bytes del comando Gree
    
    Returns:
        Paquete IR completo listo para enviar a Broadlink
    """
    # Frame 1: Header + 32 bits de datos + conector + footer
    frame1 = bytearray()
    
    # Header IR (marca larga + espacio)
    frame1.extend([0x00, (HDR_MARK >> 8) & 0xFF, HDR_MARK & 0xFF])
    frame1.append(HDR_SPACE)
    
    # 32 bits de datos (4 bytes, LSB primero)
    for byte in gree_bytes[:4]:
        for i in range(8):
            bit = (byte >> i) & 1
            frame1.append(BIT_MARK)
            frame1.append(ONE_SPACE if bit else ZERO_SPACE)
    
    # Conector de 3 bits: 0, 1, 0
    frame1.extend([BIT_MARK, ZERO_SPACE])  # bit 0
    frame1.extend([BIT_MARK, ONE_SPACE])   # bit 1
    frame1.extend([BIT_MARK, ZERO_SPACE])  # bit 0
    
    # Footer de frame 1
    frame1.append(FOOTER)
    
    # Frame break
    frame_break = bytearray([0x00, 0x02, GAP])
    
    # Calcular checksum del Frame 2: ((b0 & 0xF) + (b1 & 0xF) + 0xA) & 0xF
    checksum = ((gree_bytes[0] & 0x0F) + (gree_bytes[1] & 0x0F) + 0x0A) & 0x0F
    
    # Frame 2: 28 bits cero + 4 bits checksum (LSB first) + footer (mark + 0x00)
    frame2 = bytearray()
    
    # 28 bits de cero
    for _ in range(28):
        frame2.append(BIT_MARK)
        frame2.append(ZERO_SPACE)
    
    # 4 bits de checksum (LSB primero)
    for i in range(4):
        bit = (checksum >> i) & 1
        frame2.append(BIT_MARK)
        frame2.append(ONE_SPACE if bit else ZERO_SPACE)
    
    # Footer de frame 2 (mark + terminador)
    frame2.append(BIT_MARK)
    frame2.append(0x00)
    
    # Ensamblar datos IR
    ir_data = frame1 + frame_break + frame2
    
    # Construir paquete Broadlink completo
    packet = bytearray()
    packet.append(0x26)  # Tipo: IR
    packet.append(0x00)  # Repeat: 0
    
    # Longitud incluye ir_data + end markers (0x0D 0x05)
    total_len = len(ir_data) + 2
    packet.append(total_len & 0xFF)
    packet.append((total_len >> 8) & 0xFF)
    
    packet.extend(ir_data)
    
    # End markers
    packet.append(0x0D)
    packet.append(0x05)
    
    return bytes(packet)


def generate_payload(mode: str, temp: int, power: bool, fan: str = "auto") -> tuple:
    """
    Genera el payload completo.
    
    Returns:
        Tupla (gree_bytes, packet_bytes, base64_string)
    """
    gree_bytes = build_gree_command(mode, temp, power, fan)
    packet = encode_ir_packet(gree_bytes)
    b64 = base64.b64encode(packet).decode()
    return gree_bytes, packet, b64


def main():
    parser = argparse.ArgumentParser(
        description="Generador de payloads IR para Gree/Daitsu AC (Broadlink)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s --mode heat --temp 22 --power on
  %(prog)s --mode cool --temp 26 --power on --fan high
  %(prog)s --power off
  %(prog)s --mode heat --temp 21 --power on --output raw
        """
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["auto", "cool", "dry", "fan_only", "heat"],
        default="heat",
        help="Modo de operación (default: heat)"
    )
    
    parser.add_argument(
        "--temp", "-t",
        type=int,
        default=22,
        help="Temperatura objetivo 16-30 (default: 22)"
    )
    
    parser.add_argument(
        "--power", "-p",
        choices=["on", "off"],
        default="on",
        help="Encender o apagar (default: on)"
    )
    
    parser.add_argument(
        "--fan", "-f",
        choices=["auto", "high", "medium", "low"],
        default="auto",
        help="Velocidad del ventilador (default: auto)"
    )
    
    parser.add_argument(
        "--output", "-o",
        choices=["base64", "hex", "raw", "all"],
        default="base64",
        help="Formato de salida (default: base64)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Solo mostrar el payload, sin información adicional"
    )
    
    args = parser.parse_args()
    
    # Validar temperatura
    if args.temp < 16 or args.temp > 30:
        print(f"Error: La temperatura debe estar entre 16 y 30 (recibido: {args.temp})", file=sys.stderr)
        sys.exit(1)
    
    power = args.power == "on"
    gree_bytes, packet, b64 = generate_payload(args.mode, args.temp, power, args.fan)
    
    if args.quiet:
        if args.output == "base64":
            print(b64)
        elif args.output == "hex":
            print(packet.hex())
        elif args.output == "raw":
            print(' '.join(f'{b:02X}' for b in packet))
        else:
            print(b64)
    else:
        print("=" * 60)
        print("GREE/DAITSU IR PAYLOAD GENERATOR")
        print("=" * 60)
        print(f"Modo:        {args.mode}")
        print(f"Temperatura: {args.temp}°C")
        print(f"Power:       {'ON' if power else 'OFF'}")
        print(f"Ventilador:  {args.fan}")
        print("-" * 60)
        print(f"Gree bytes:  {' '.join(f'{b:02X}' for b in gree_bytes)}")
        print(f"Longitud:    {len(packet)} bytes")
        print("-" * 60)
        
        if args.output in ["base64", "all"]:
            print(f"Base64:\n{b64}")
        
        if args.output in ["hex", "all"]:
            print(f"\nHex:\n{packet.hex()}")
        
        if args.output in ["raw", "all"]:
            print(f"\nRAW (bytes):\n{' '.join(f'{b:02X}' for b in packet)}")
        
        print("=" * 60)
        print("\nPara usar en Home Assistant (service call):")
        print(f"""
service: remote.send_command
target:
  entity_id: remote.tu_broadlink_rm4c
data:
  command: "b64:{b64}"
""")


if __name__ == "__main__":
    main()
