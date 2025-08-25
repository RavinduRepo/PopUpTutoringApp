# base_listener.py
import time
import threading
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseEventListener(ABC):
    """Base class for event listeners with common functionality"""
    
    def __init__(self):
        logger.info("Initialized base event listener")
        self.listeners = {}
        self.is_running = False
        self.listener_thread = None
    
    def subscribe(self, event_type, listener):
        """Subscribe to an event type"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
    
    def _notify(self, event_type, data):
        """Notify all subscribers of an event"""
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                try:
                    listener(data)
                except Exception as e:
                    logger.error(f"Error in listener callback: {e}")
    
    @abstractmethod
    def start_listening(self):
        """Start listening for events"""
        pass
    
    @abstractmethod
    def stop_listening(self):
        """Stop listening for events"""
        pass