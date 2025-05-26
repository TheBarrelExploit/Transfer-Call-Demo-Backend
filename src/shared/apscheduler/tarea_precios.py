from datetime import datetime, timezone
from src.shared.database.mongodb import MongoDB
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

logger = logging.getLogger(__name__)

async def execute_price_change(job_id: str):
    try:
        mongo = MongoDB()
        client = mongo.get_database()
        collection = client.prices_changes
        collection_price = client.price
        collection_history = client["price history"]

        # Obtener el documento completo primero
        bulk_data = await collection.find_one({"_id": job_id})
        
        if not bulk_data:
            logger.error(f"No se encontró el documento con id {job_id}")
            return

        # Verificar si existe el campo 'change' y es iterable
        if "change" not in bulk_data or not isinstance(bulk_data["change"], list):
            logger.error(f"Documento {job_id} no contiene cambios válidos")
            return

        # Procesar cada cambio (ahora bulk_data["change"] es una lista)
        for change in bulk_data["change"]:
            try:
                await update_single_price(
                    call_type=change["call_type"],
                    new_rate=change["rate_per_minute"],
                    divisa=change["divisa"],
                    user=bulk_data["user"],
                    collection_price=collection_price,
                    collection_history=collection_history
                )
                logger.info(f"Cambio para {change['call_type']} completado")
            except Exception as e:
                logger.error(f"Error actualizando {change['call_type']}: {str(e)}")
                continue  # Continuar con los siguientes cambios

        # Marcar como completado
        await collection.update_one(
            {"_id": job_id}, 
            {"$set": {"status": "completed"}}
        )
        logger.info(f"Cambio de precios {job_id} completado correctamente")

    except Exception as e:
        logger.error(f"Error en execute_price_change: {str(e)}")
        raise

async def update_single_price(
    call_type: str, 
    new_rate: int, 
    divisa: str, 
    user: str, 
    collection_price: AsyncIOMotorCollection, 
    collection_history: AsyncIOMotorCollection
):
    current_price = await collection_price.find_one({"call_type": call_type})
    current_price.pop("_id")

    if not current_price:
        raise ValueError(f"No se encontró el precio para {call_type}")

    # Crear registro histórico
    await collection_history.insert_one({
        **current_price,
        "valid_until": datetime.now(timezone.utc),
        "is_active": False,
        "modified_by": user,
        "modification_date": datetime.now(timezone.utc)
    })

    # Actualizar precio actual
    await collection_price.update_one(
        {"call_type": call_type},
        {
            "$set": {
                "rate_per_minute": new_rate,
                "divisa": divisa,
                "valid_from": datetime.now(timezone.utc),
                "last_modified_by": user,
                "last_modified": datetime.now(timezone.utc)
            }
        }
    )