import asyncio
import logging.config
import os
from pathlib import Path

from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.symphony_bdk import SymphonyBdk


async def run():
    stream_id_1 = "lRwCZlDbxWLd2BDP-1D_8n___o0f4ZkEdA"
    stream_id_2 = "12lruitZ3cecVY1_SKgKB3___omJ6uHodA"

    config = BdkConfigLoader.load_from_symphony_dir("config.yaml")

    async with SymphonyBdk(config) as bdk:
        message_service = bdk.messages()

        await message_service.send_message(stream_id_1, "<messageML>Hello, World!</messageML>")

        with open("/path/to/attachment1", "rb") as file1, \
                open("/path/to/attachment2", "rb") as file2:
            await message_service.blast_message(
                [stream_id_1, stream_id_2],
                "<messageML>Hello, World!</messageML>",
                attachment=[file1, file2]
            )

        logging.info("Obo example:")
        obo_auth_session = bdk.obo(username="username")
        async with bdk.obo_services(obo_auth_session) as obo_services:
            # Message ID can be retrieved by following guide here:
            # https://docs.developers.symphony.com/building-bots-on-symphony/datafeed/overview-of-streams
            await obo_services.messages().suppress_message("URL-Safe MessageID")

logging.config.fileConfig(Path(__file__).parent.parent / "logging.conf", disable_existing_loggers=False)

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(run())
