import argparse

def get_settings():
    parser = argparse.ArgumentParser(description="Debug argparse")
    parser.add_argument("--path", type=str, help="Path to the USD file (default: ./example.usd)")
    parser.add_argument("--output_path", type=str, help="Output file path (default: output.png)")
    parser.add_argument("-s", "--size", type=int, default=1024, help="Image size")

    args = parser.parse_args()

    # Apply defaults if arguments are None
    args.path = args.path or "./example.usd"
    args.output_path = args.output_path or "output.png"

    print(args)
    return args

if __name__ == "__main__":
    args = get_settings()
    print("Parsed arguments:", args)
