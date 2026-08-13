"""Adaptador de eventos: registra eventos estructurados, reemplazable por un broker."""

import logging


class LoggingEventPublisher:
    def publish(self, name: str, payload: dict[str, str]) -> None:
        logging.getLogger("orders.events").info("event=%s payload=%s", name, payload)
