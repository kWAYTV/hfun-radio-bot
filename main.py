# Imports
import os, discord, asyncio
from loguru import logger
from traceback import format_exc
from discord.ext import commands
from src.helper.config import Config
from src.database.loader import DatabaseLoader
from src.manager.file_manager import FileManager

# Set logging system handler
logger.add(Config().log_file, mode="w+")

# Define the bot & load the commands, events and loops
class Bot(commands.Bot):
    def __init__(self) -> None:
        self.file_manager = FileManager()
        self.command_queue = asyncio.Queue()
        super().__init__(command_prefix=Config().bot_prefix, help_command=None, intents=discord.Intents.all())

    # Function to load the extensions
    async def setup_hook(self) -> None:
        try:
            os.system("cls||clear")
            logger.info("Starting bot...")

            # Check for file inputs
            logger.debug("Checking for file inputs...")
            self.file_manager.check_input()

            # Set-up the database
            logger.debug("Setting up databases...")
            await DatabaseLoader().setup()

            # Load the cogs
            logger.debug("Loading cogs...")
            for filename in os.listdir("./src/cogs/commands"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    await self.load_extension(f"src.cogs.commands.{filename[:-3]}")

            # Load the events
            logger.debug("Loading events...")
            for filename in os.listdir("./src/cogs/events"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    await self.load_extension(f"src.cogs.events.{filename[:-3]}")

            # Load the loops
            logger.debug("Loading loops...")
            for filename in os.listdir("./src/cogs/loops"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    await self.load_extension(f"src.cogs.loops.{filename[:-3]}")

            # Start the command worker
            self.loop.create_task(self.command_worker())

            # Done!
            logger.info("Setup completed!")
        except Exception:
            logger.critical(f"Error setting up bot: {format_exc()}")
            exit()

    async def command_worker(self):
        while True:
            interaction, coro = await self.command_queue.get()
            try:
                await coro
            except discord.errors.NotFound as e:
                await self.handle_not_found_error(interaction, e)
            except Exception as e:
                await self.handle_generic_error(interaction, e)
            finally:
                self.command_queue.task_done()

    async def handle_not_found_error(self, interaction, error):
        logger.critical(f"Failed to respond to interaction: {error}")
        await self.send_followup_error_message(interaction, "An error occurred while executing your command. Please notify an Admin.")

    async def handle_generic_error(self, interaction, error):
        logger.critical(f"Unexpected error: {error}")
        await self.send_followup_error_message(interaction, "An error occurred while executing your command. Please notify an Admin.")

    async def send_followup_error_message(self, interaction, message):
        if hasattr(interaction, 'followup') and not interaction.response.is_done():
            try:
                await interaction.followup.send(message, ephemeral=True)
            except Exception as followup_error:
                logger.critical(f"Failed to send follow-up message: {followup_error}")

    # Function to shutdown the bot
    async def close(self) -> None:
        await super().close()

# Run the bot
if __name__ == "__main__":
    try:
        bot = Bot()
        bot.run(Config().bot_token)
    except KeyboardInterrupt:
        logger.critical("Goodbye!")
        exit()
    except Exception:
        logger.critical(f"Error running bot: {format_exc()}")
        exit()
