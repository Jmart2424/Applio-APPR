from edge_tts.list_voices import list_voices
import asyncio

async def get_voices():
    voices = await list_voices()
    print("\nAvailable English Male Voices:")
    print("-----------------------------")
    for voice in voices:
        if 'en-US' in voice['ShortName'] and voice['Gender'] == 'Male':
            print(f"Name: {voice['ShortName']}")
            print(f"Gender: {voice['Gender']}")
            print(f"Locale: {voice['Locale']}")
            print("-----------------------------")

if __name__ == "__main__":
    asyncio.run(get_voices())
