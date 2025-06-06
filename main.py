#!.venv/bin/python3

import checkege.cli as c
import asyncio

async def main():
    cli = c.Cli()
    await cli.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{c.RESET_COLOR}{c.GRAY}{c.ITALIC}Прерывание пользователем.{c.RESET_COLOR}")
        exit(0)    
