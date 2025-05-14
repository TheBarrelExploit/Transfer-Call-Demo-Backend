from fastapi import Request
from datetime import datetime, timezone
from src.shared.database.mongodb import MongoDB
from motor.motor_asyncio import  AsyncIOMotorCollection
import logging

logger = logging.getLogger(__name__)

async def execute_price_change(job_id: str):
    
    client:MongoDB = Request.app.state.mongo
    collection:AsyncIOMotorCollection = client.get_collection("prices_change")
    collection_price:AsyncIOMotorCollection = client.get_collection("price")
    collection_history:AsyncIOMotorCollection = client.get_collection("price history")

    
    bulk_data = await collection.find({"_id": job_id})

    async for change in bulk_data["change"]:
        try:
            update_single_price(
                call_type=change["call_type"],
                new_rate=change["rate_per_minute"],
                divisa=change["divisa"],
                user=bulk_data["user"],
                collection_price=collection_price,
                collection_history=collection_history
                )
            logger.info(f"Cambio de precios {job_id} completado correctamente")
        except Exception as e:
                print(f"Error actualizando el {change['call_type']}: {str(e)}")
      
    await collection.update_one(
            {"_id": job_id}, {"$set": {"status": "completed"}}
    )

async def update_single_price(
      call_type: str, new_rate: int, divisa: str, user: str, collection_price:AsyncIOMotorCollection, collection_history:AsyncIOMotorCollection
    ):
        current_price = await collection_price.find_one({"call_type": call_type})

        if not current_price:
            raise ValueError(f"No se encontró el precio para el tipo de llamada {call_type}")

        await collection_history.insert_one(
            {**current_price, "valid_to": datetime.now(timezone.utc),"user": user}
        )

        await collection_price.update_one(
            {"call_type": call_type},
            {
                "$set": {
                    "rate_per_minute": new_rate,
                    "divisa": divisa,
                    "valid_from": datetime.now(timezone.utc),
                }
            },
        )
