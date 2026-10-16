import argparse

from .server import make_server


def main():
    parser = argparse.ArgumentParser(description="Run the local AUTOSIM mission workspace.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default="data/autosim.sqlite3")
    args = parser.parse_args()
    server = make_server(args.host, args.port, args.db)
    print(f"AUTOSIM available at http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
