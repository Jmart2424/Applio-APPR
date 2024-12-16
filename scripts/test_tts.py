import asyncio
import time
import edge_tts

async def test_synthesis():
    start_time = time.time()

    # Test text
    text = "Hello world, this is a test of the TTS system."
    voice = "en-US-JennyNeural"

    # Create communicator
    communicate = edge_tts.Communicate(text, voice)

    # Perform synthesis
    await communicate.save("test_output.wav")

    end_time = time.time()
    synthesis_time = end_time - start_time

    print(f"Synthesis completed in {synthesis_time:.2f} seconds")
    return synthesis_time

if __name__ == "__main__":
    asyncio.run(test_synthesis())
