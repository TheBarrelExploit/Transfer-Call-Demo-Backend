import os
import gc
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from typing import Iterator
from pymongo import MongoClient

root = os.path.join(
    os.path.dirname(__file__), "files/SSM1PO_0_2025-04-14-09-54-46-719_All_MCPV4.closed"
)


def get_time_difference(
    start_time: str, end_time: str
) -> tuple[str, datetime, datetime]:
    """_summary_

    Args:
        start_time (str): _description_
        end_time (str): _description_

    Returns:
        tuple[str, datetime, datetime]: _description_
    """
    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    delta = end - start
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return formatted_time, start, end


def parse_xml_file(
    xml_path: str,
) -> tuple[
    dict[str, dict[str, dict]], dict[str, dict[str, dict]], dict[str, dict[str, dict]]
]:
    """_summary_

    Args:
        xml_path (str): _description_

    Returns:
        tuple[ dict[str, dict[str, dict]], dict[str, dict[str, dict]], dict[str, dict[str, dict]]]: _description_
    """
    namespaces = {"xsi": "http://www.w3.org/2001/XMLSchema-instance"}

    voip_records_ingress = defaultdict(dict)
    voip_records_egress = defaultdict(dict)
    routing_records = defaultdict(dict)

    mapping = {
        "ConnectIngress": (voip_records_ingress, "start"),
        "DisconnectIngress": (voip_records_ingress, "end"),
        "ConnectEgress": (voip_records_egress, "start"),
        "DisconnectEgress": (voip_records_egress, "end"),
    }

    id_fields = {"nortel:Nortel-VoIP": "corrID", "nortel:Nortel-Routing": "recordID"}

    for event, elem in ET.iterparse(xml_path, events=("end",)):
        if "}IPDR" in elem.tag:
            elem_type = elem.get(f"{{{namespaces['xsi']}}}type")

            if elem_type in ["nortel:Nortel-VoIP", "nortel:Nortel-Routing"]:
                record_id = None
                record_data = {}

                id_field = id_fields.get(elem_type)

                for child in elem:
                    tag = child.tag.split("}")[1] if "}" in child.tag else child.tag
                    if tag == id_field and child.text:
                        record_id = child.text.strip()
                    record_data[tag] = child.text.strip() if child.text else None

                if elem_type == "nortel:Nortel-VoIP" and record_id:
                    call_status = record_data.get("recordType")

                    if call_status in mapping:
                        dictionary, key = mapping[call_status]
                        dictionary[record_id][key] = record_data

                if elem_type == "nortel:Nortel-Routing":
                    routing_records[record_id][record_data.get("routingID")] = (
                        record_data
                    )

            elem.clear()

    ingress_calls = dict(voip_records_ingress)
    egress_calls = dict(voip_records_egress)
    routing_calls = dict(routing_records)

    gc.collect()
    voip_records_egress.clear()
    voip_records_ingress.clear()
    routing_records.clear()

    return (ingress_calls, egress_calls, routing_calls)


def process_call_data(xml_path: str) -> Iterator[dict]:
    """_summary_

    Args:
        xml_path (str): _description_

    Yields:
        Iterator[dict]: _description_
    """
    ingress, egress, routing = parse_xml_file(xml_path=xml_path)

    for key, data in egress.items():
        egress_data_start = data.get("start", {})
        # egress_data_end = data.get("end", {})
        ingress_data = ingress.get(key, {})
        ingress_data_start = ingress_data.get("start", {})
        ingress_data_end = ingress_data.get("end", {})

        subscriber_fqdn = ingress_data_start.get("subscriberFQDN")

        user_data_dialed = ingress_data_start.get("subscriberID", "")
        unique_call_id_ingress = ingress_data_start.get("uniqueCallId")
        unique_call_id_egress = egress_data_start.get("uniqueCallId")
        dialed_info = parse_user_data(user_data_dialed)
        dialed_number = dialed_info["number"]
        entity_dialed = dialed_info["entity"]

        error_code = ingress_data_start.get("proprietaryErrorCode")
        is_error_call = error_code is not None

        record_id = egress_data_start.get("recordID")
        routing_entries: dict[str, dict] = routing.get(record_id, {})

        if is_error_call:
            user_data_connect = ingress_data_start.get("originalDestinationId", "")
            connect_info = parse_user_data(
                user_data=user_data_connect, is_destination=True
            )
            connect_number = connect_info["number"]
            entity_connect = connect_info["entity"]

            start_time: str = ingress_data_start.get("startTime")
            end_time: str = ingress_data_start.get("recTime")

            dt_start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            dt_end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

            for route_idx, routing_data in routing_entries.items():
                feature = routing_data.get("routingReason")

                call_record = {
                    "dialed_number": dialed_number,
                    "connect_number": connect_number,
                    "entity_dialed": entity_dialed,
                    "entity_connect": entity_connect,
                    "corr_id": key,
                    "start_date": dt_start_time,
                    "end_date": dt_end_time,
                    "feature": feature,
                    "entity_zone": subscriber_fqdn,
                    "routing_id": route_idx,
                    "erorr_code": error_code,
                    "record_id": record_id,
                    "unique_call_id_ingress": unique_call_id_ingress,
                    "unique_call_id_egress": unique_call_id_egress,
                }
                yield call_record
        else:
            start_time = ingress_data_start.get("recTime")
            end_time = ingress_data_end.get("recTime")

            duration, start_date, end_date = get_time_difference(
                start_time=start_time, end_time=end_time
            )

            connected_number_copy = None
            for route_idx, routing_data in routing_entries.items():
                print(route_idx)
                feature = routing_data.get("routingReason")
                info = routing_data.get("routingDest")

                connected_number = None
                entity_connected = None

                if info:
                    connect_info = parse_routing_dest(info)
                    connected_number = connect_info["number"]
                    entity_connected = connect_info["entity"]

                effective_dialed_number = connected_number_copy or dialed_number

                call_record = {
                    "dialed_number": effective_dialed_number,
                    "connected_number": connected_number,
                    "dialed_entity": entity_dialed,
                    "connected_entity": entity_connected,
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration": duration,
                    "corr_id": key,
                    "call_progress_state": ingress_data_end.get("callProgressState"),
                    "call_completion_code": ingress_data_end.get("callCompletionCode"),
                    "feature": feature,
                    "entity_zone": subscriber_fqdn,
                    "routing_id": route_idx,
                    "record_id": record_id,
                    "unique_call_id_ingress": unique_call_id_ingress,
                    "unique_call_id_egress": unique_call_id_egress,
                }
                yield call_record

                connected_number_copy = connected_number


def parse_user_data(user_data: str, is_destination: bool = False) -> dict:
    """Procesa los datos de usuarios desde un string en formato user@domain"""

    if not user_data:
        return {"number": None, "entity": None}

    parts: list[str] = user_data.split("@")

    if len(parts) < 2:
        return {"number": parts[0], "entity": None}

    number: str = parts[0]
    entity: str = parts[1].split(".")[0]

    if is_destination and ":" in number:
        number = number.split(":")[1]

    return {"number": number, "entity": entity}


def parse_routing_dest(routing_dest: str) -> dict:
    """Procesa los datos de routing desde un string en formato sip:number@domain"""
    if not routing_dest:
        return {"number": None, "entity": None}

    try:
        number_part = routing_dest.split("@", 1)[0]
        number = number_part.split(":", 1)[1] if ":" in number_part else number_part

        domain_part = routing_dest.split("@")[1]
        entity_parts = domain_part.split(".")
        entity = ".".join(entity_parts[:2])

        return {"number": number, "entity": entity}
    except (IndexError, AttributeError):
        return {"number": None, "entity": None}


def save_to_mongodb(
    data_records: list, collection_name: str = "registros", batch_size: int = 1000
) -> int:
    """
    Guarda los registros en MongoDB usando procesamiento por lotes

    Args:
        data_records: Iterable (lista o generador) con los registros a guardar
        collection_name:str Nombre de la colección en MongoDB
        batch_size:int Tamaño del lote para la inserción
    Returns:
        inserted_count:int Numero total de registro insertados en MongoDB
    """
    try:
        # Configuración de MongoDB
        client = MongoClient("mongodb://root:root123@localhost:27017/")
        db = client["registros_llamadas"]
        collection = db[collection_name]

        batch = []
        inserted_count = 0

        for record in data_records:
            batch.append(record)

            if len(batch) >= batch_size:
                collection.insert_many(batch, ordered=False)
                inserted_count += len(batch)
                print(f"Insertados {inserted_count} registros en MongoDB")
                batch = []

        if batch:
            collection.insert_many(batch)
            inserted_count += len(batch)
            print(f"Insertados {inserted_count} registros en MongoDB (lote final)")

        print(f"Total de registros guardados en MongoDB: {inserted_count}")
        return inserted_count

    except Exception as e:
        print(f"Error al guardar en MongoDB: {e}")
        return 0


def main(xml_path, collection_name="registros", batch_size=1000):
    """
    Función principal que procesa el archivo XML y guarda los resultados en MongoDB

    Args:
        xml_path: Ruta al archivo XML a procesar
        collection_name: Nombre de la colección en MongoDB
        batch_size: Tamaño del lote para inserción en MongoDB
    """
    try:
        # Medir tiempo de ejecución
        start_time = time.time()

        # Procesar y guardar datos usando el generador
        record_count = save_to_mongodb(
            process_call_data(xml_path),
            collection_name=collection_name,
            batch_size=batch_size,
        )

        elapsed_time = time.time() - start_time
        print(f"Procesamiento completado en {elapsed_time:.2f} segundos")
        print(f"Velocidad: {record_count / elapsed_time:.2f} registros/segundo")
    except Exception as e:
        print(f"Error en el procesamiento: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    total_start_time = time.time()
    main(root, "llamadas")
    total_elapsed_time = time.time() - total_start_time
    print(f"Tiempo total de ejecución del programa:{total_elapsed_time:.2f}")
