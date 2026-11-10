import asyncio
import time
import threading

async def order(food):
    print(f"Ordered: {food:<7} | Thread: {threading.current_thread().name}")
    await asyncio.sleep(3)  # Non-blocking simulated wait for kitchen
    print(f"Ready:   {food:<7} | Thread: {threading.current_thread().name}")

async def main():
    # Run all three orders concurrently inside the Single-Threaded Event Loop
    await asyncio.gather(
        order("Tea"),
        order("Biryani"),
        order("Coffee")
    )

start = time.time()
asyncio.run(main())
print(f"Total time: {time.time() - start:.2f} seconds (Single Thread Concurrency!)")