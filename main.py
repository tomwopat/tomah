import asyncio
import logging
import pprint

from tomah import Client


async def amain():
    # set the logging level to DEBUG
    logging.basicConfig(level=logging.DEBUG)
    t = Client(
    )
    await t.regions()
    print(f"me: {pprint.pformat(await t.me())}")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
