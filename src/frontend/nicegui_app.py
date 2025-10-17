"""
NiceGUI Frontend
Dark-mode UI with file upload, document viewer, chat interface, logs, and system flags.
"""

import asyncio
from pathlib import Path
from typing import Optional, List
from nicegui import ui, app
import uuid

from ..common import logger, config, storage, ui_log_bridge
from ..agents.ingestion_agent import IngestionAgent
from ..agents.rag_agent import RAGAgent


class NiceGUIApp:
    """Main NiceGUI application."""
    
    def __init__(self):
        self.ingestion_agent = IngestionAgent()
        self.rag_agent = RAGAgent()
        self.current_session_id = None
        self.log_messages = []
        self.chat_container = None
        self.pipeline = None
        
        # Register log callback
        ui_log_bridge.register_callback(self.on_log_message)
    
    def on_log_message(self, level: str, message: str):
        """Handle log messages from agents."""
        self.log_messages.append({
            "level": level,
            "message": message,
            "timestamp": ""
        })
        # Keep only last 100 messages
        if len(self.log_messages) > 100:
            self.log_messages = self.log_messages[-100:]
    
    async def upload_files(self, content: bytes, name: str):
        """Handle file uploads."""
        if name.lower().endswith('.pdf'):
            # Determine language from dropdown or default to 'en'
            language = self.upload_language_select.value
            
            # Save to incoming directory
            incoming_dir = config.get_incoming_dir(language)
            dest_path = incoming_dir / name
            
            # Write file
            with open(dest_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Uploaded {name} to {language} directory", to_ui=True)
            ui.notify(f"Uploaded {name}", type="positive")
            
            # Process file
            await self.ingestion_agent.process_new_file(dest_path)
        else:
            ui.notify(f"Skipped {name} (not a PDF)", type="warning")
    
    async def send_message(self):
        """Send chat message."""
        query = self.chat_input.value.strip()
        
        if not query:
            return
        
        # Clear input
        self.chat_input.value = ""
        
        # Create session if needed
        if not self.current_session_id:
            self.current_session_id = str(uuid.uuid4())
        
        # Add user message to UI
        with self.chat_container:
            ui.chat_message(query, name="You", sent=True)
        
        # Add placeholder for assistant response
        with self.chat_container:
            response_container = ui.chat_message(name="Assistant", sent=False)
            response_label = ui.label("Thinking...")
        
        # Stream response
        full_response = ""
        
        async for chunk in self.rag_agent.chat(query, self.current_session_id, stream=True):
            if chunk["type"] == "response":
                content = chunk["content"]
                full_response += content
                response_label.text = full_response
            elif chunk["type"] == "status":
                response_label.text = chunk["message"]
            elif chunk["type"] == "error":
                response_label.text = f"Error: {chunk['message']}"
                ui.notify(chunk["message"], type="negative")
    
    def clear_chat(self):
        """Clear chat session."""
        if self.current_session_id:
            asyncio.create_task(storage.clear_session(self.current_session_id))
        self.current_session_id = None
        self.chat_container.clear()
        ui.notify("Chat cleared", type="info")
    
    def create_ui(self):
        """Create the main UI."""
        # Dark theme
        ui.dark_mode().enable()
        
        # Page title and header
        with ui.header().classes('items-center justify-between'):
            ui.label('Multilingual Agentic RAG').classes('text-h4')
            ui.badge('v1.0', color='green')
        
        # Main layout with tabs
        with ui.tabs().classes('w-full') as tabs:
            upload_tab = ui.tab('📤 Upload')
            chat_tab = ui.tab('💬 Chat')
            docs_tab = ui.tab('📚 Documents')
            logs_tab = ui.tab('📋 Logs')
            config_tab = ui.tab('⚙️ Config')
        
        with ui.tab_panels(tabs, value=chat_tab).classes('w-full'):
            # Upload Tab
            with ui.tab_panel(upload_tab):
                ui.label('Upload PDF Documents').classes('text-h5')
                ui.markdown('Upload PDF files to be processed and indexed.')
                
                with ui.row().classes('items-center gap-4'):
                    ui.label('Language:')
                    self.upload_language_select = ui.select(
                        options=['en', 'zh', 'hi', 'bn', 'ur'],
                        value='en',
                        label='Document Language'
                    ).classes('w-32')
                
                ui.upload(
                    on_upload=lambda e: asyncio.create_task(self.upload_files(e.content, e.name)),
                    multiple=True,
                    auto_upload=True,
                    label='Select PDF Files'
                ).props('accept=.pdf').classes('max-w-lg')
                
                ui.separator()
                
                ui.label('Processing Queue').classes('text-h6 mt-4')
                
                with ui.row():
                    ui.button('Scan Existing Files', 
                             on_click=lambda: asyncio.create_task(self.ingestion_agent.scan_existing_files()))
                    ui.button('Refresh Status', on_click=lambda: ui.notify('Queue status updated'))
            
            # Chat Tab
            with ui.tab_panel(chat_tab):
                ui.label('Chat with Documents').classes('text-h5')
                
                # Chat container
                self.chat_container = ui.column().classes('w-full h-96 overflow-y-auto bg-gray-900 rounded p-4')
                
                # Input area
                with ui.row().classes('w-full items-center gap-2 mt-4'):
                    self.chat_input = ui.input(
                        placeholder='Ask a question about your documents...'
                    ).classes('flex-grow').on('keydown.enter', lambda: asyncio.create_task(self.send_message()))
                    
                    ui.button('Send', on_click=lambda: asyncio.create_task(self.send_message())).props('icon=send')
                    ui.button('Clear', on_click=self.clear_chat).props('icon=delete color=red')
            
            # Documents Tab
            with ui.tab_panel(docs_tab):
                ui.label('Document Library').classes('text-h5')
                ui.markdown('View indexed documents and their metadata.')
                
                with ui.column().classes('w-full'):
                    ui.label('Coming soon: Document browser and metadata viewer')
                    
                    # Placeholder for document list
                    with ui.expansion('Sample Documents', icon='folder').classes('w-full'):
                        ui.label('No documents indexed yet.')
            
            # Logs Tab
            with ui.tab_panel(logs_tab):
                ui.label('System Logs').classes('text-h5')
                
                with ui.row():
                    ui.button('Refresh', on_click=lambda: self.refresh_logs()).props('icon=refresh')
                    ui.button('Clear', on_click=lambda: self.log_messages.clear()).props('icon=delete')
                
                # Log container
                self.log_container = ui.column().classes('w-full h-96 overflow-y-auto bg-gray-900 rounded p-4 font-mono text-sm')
                
                # Auto-refresh timer
                ui.timer(2.0, lambda: self.refresh_logs())
            
            # Config Tab
            with ui.tab_panel(config_tab):
                ui.label('System Configuration').classes('text-h5')
                
                with ui.grid(columns=2).classes('w-full gap-4'):
                    # LLM Settings
                    with ui.card().classes('p-4'):
                        ui.label('LLM Settings').classes('text-h6')
                        ui.label(f'Primary: {config.llm_primary}')
                        ui.label(f'Fallback: {config.llm_fallback}')
                        ui.label(f'Ollama Host: {config.ollama_host}')
                    
                    # Retrieval Settings
                    with ui.card().classes('p-4'):
                        ui.label('Retrieval Settings').classes('text-h6')
                        ui.label(f'BM25 Enabled: {config.enable_bm25}')
                        ui.label(f'Fusion Method: {config.fusion_method}')
                        ui.label(f'Rerank: {config.enable_rerank}')
                    
                    # Embedding Settings
                    with ui.card().classes('p-4'):
                        ui.label('Embedding Settings').classes('text-h6')
                        ui.label(f'Model: {config.embedding_model}')
                        ui.label(f'API Keys: {len(config.get_gemini_keys())} configured')
                    
                    # System Settings
                    with ui.card().classes('p-4'):
                        ui.label('System Settings').classes('text-h6')
                        ui.label(f'GPU Enabled: {config.enable_gpu}')
                        ui.label(f'Platform: {config.gpu_platform}')
                        ui.label(f'Qdrant: {config.qdrant_url}')
        
        # Footer
        with ui.footer().classes('bg-gray-800'):
            ui.label('Multilingual Agentic RAG System | Powered by Gemini, DeepSeek-R1, Qdrant').classes('text-sm text-gray-400')
    
    def refresh_logs(self):
        """Refresh log display."""
        self.log_container.clear()
        
        with self.log_container:
            for log in self.log_messages[-50:]:  # Show last 50
                level = log["level"]
                message = log["message"]
                
                # Color code by level
                color = {
                    "info": "text-cyan-400",
                    "warning": "text-yellow-400",
                    "error": "text-red-400",
                    "success": "text-green-400",
                    "debug": "text-gray-500"
                }.get(level, "text-white")
                
                ui.label(f"[{level.upper()}] {message}").classes(color)
    
    async def initialize_pipeline(self):
        """Initialize the document processing pipeline."""
        from ..main import DocumentProcessingPipeline
        
        logger.info("Initializing document processing pipeline...")
        self.pipeline = DocumentProcessingPipeline()
        await self.pipeline.initialize()
        
        # Start background processing
        await self.pipeline.start_processing()
        logger.success("Pipeline initialized and processing started!")
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the NiceGUI app."""
        self.create_ui()
        
        # Schedule initialization on startup
        app.on_startup(storage.initialize)
        app.on_startup(self.ingestion_agent.initialize)
        app.on_startup(self.initialize_pipeline)
        
        logger.info(f"Starting NiceGUI app on http://{host}:{port}")
        ui.run(host=host, port=port, title="Multilingual RAG", dark=True, reload=False)


def start_app():
    """Start the NiceGUI application."""
    app_instance = NiceGUIApp()
    app_instance.run()


if __name__ == "__main__":
    start_app()

