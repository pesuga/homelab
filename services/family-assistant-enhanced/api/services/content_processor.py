"""
Multimodal content processing services.

Handles:
- Image content analysis using vision models
- Audio transcription using speech recognition
- Document text extraction and summarization
- Content safety and moderation
- File storage and management
"""

import os
import uuid
import hashlib
import asyncio
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, BinaryIO, Union
from datetime import datetime, timedelta
from enum import Enum
import mimetypes
import aiofiles
import aiohttp
from PIL import Image, ImageOps
import PyPDF2
import docx
from pydub import AudioSegment

from ..models.multimodal import (
    ContentType, ProcessingStatus, MultimodalContent,
    TextContent, ImageContent, AudioContent, DocumentContent,
    MediaMetadata, ContentProcessingResult, FamilyMemberProfile
)
from ..models.database import (
    ContentUpload, ContentProcessingJob, FamilyMember,
    create_content_processing_result
)
from settings import settings


class ContentProcessorError(Exception):
    """Base exception for content processing errors."""
    pass


class UnsupportedContentTypeError(ContentProcessorError):
    """Raised when content type is not supported."""
    pass


class FileSizeExceededError(ContentProcessorError):
    """Raised when file size exceeds limits."""
    pass


class ProcessingTimeoutError(ContentProcessorError):
    """Raised when content processing times out."""
    pass


class ContentProcessor:
    """Main content processor for multimodal content."""

    def __init__(self, storage_path: str = "uploads"):
        """Initialize content processor."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        # Content size limits (in bytes)
        self.max_file_sizes = {
            ContentType.IMAGE: 50 * 1024 * 1024,      # 50MB
            ContentType.AUDIO: 100 * 1024 * 1024,     # 100MB
            ContentType.VIDEO: 500 * 1024 * 1024,     # 500MB
            ContentType.DOCUMENT: 100 * 1024 * 1024,   # 100MB
        }

        # Supported file formats
        self.supported_formats = {
            ContentType.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            ContentType.AUDIO: ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
            ContentType.VIDEO: ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            ContentType.DOCUMENT: ['.pdf', '.docx', '.txt', '.md', '.rtf']
        }

    async def process_content(
        self,
        file_data: bytes,
        filename: str,
        family_member: FamilyMemberProfile,
        conversation_id: Optional[str] = None
    ) -> ContentProcessingResult:
        """Process uploaded multimodal content."""

        # Determine content type
        content_type = self._detect_content_type(filename, file_data)

        # Validate file size
        self._validate_file_size(file_data, content_type)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = Path(filename).suffix.lower()
        stored_filename = f"{file_id}{extension}"
        file_path = self.storage_path / stored_filename

        # Save file to storage
        await self._save_file(file_data, file_path)

        # Create database record
        upload = await self._create_upload_record(
            filename=filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
            content_type=content_type,
            file_data=file_data,
            family_member=family_member,
            conversation_id=conversation_id
        )

        # Process content based on type
        try:
            if content_type == ContentType.IMAGE:
                result = await self._process_image(upload)
            elif content_type == ContentType.AUDIO:
                result = await self._process_audio(upload)
            elif content_type == ContentType.DOCUMENT:
                result = await self._process_document(upload)
            else:
                result = await self._process_generic_file(upload)

        except Exception as e:
            # Update record with error
            upload.processing_status = ProcessingStatus.FAILED
            upload.processing_error = str(e)
            # Save to database here
            raise ContentProcessorError(f"Failed to process {content_type.value}: {str(e)}")

        return result

    def _detect_content_type(self, filename: str, file_data: bytes) -> ContentType:
        """Detect content type from filename and data."""
        # Try MIME type first
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            if mime_type.startswith('image/'):
                return ContentType.IMAGE
            elif mime_type.startswith('audio/'):
                return ContentType.AUDIO
            elif mime_type.startswith('video/'):
                return ContentType.VIDEO
            elif mime_type in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return ContentType.DOCUMENT

        # Fallback to file extension
        extension = Path(filename).suffix.lower()
        for content_type, extensions in self.supported_formats.items():
            if extension in extensions:
                return content_type

        # Default to file
        return ContentType.FILE

    def _validate_file_size(self, file_data: bytes, content_type: ContentType):
        """Validate file size against limits."""
        file_size = len(file_data)
        max_size = self.max_file_sizes.get(content_type, self.max_file_sizes[ContentType.FILE])

        if file_size > max_size:
            raise FileSizeExceededError(
                f"File size {file_size} bytes exceeds maximum {max_size} bytes for {content_type.value}"
            )

    async def _save_file(self, file_data: bytes, file_path: Path):
        """Save file data to storage."""
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)

    async def _create_upload_record(
        self,
        filename: str,
        stored_filename: str,
        file_path: str,
        content_type: ContentType,
        file_data: bytes,
        family_member: FamilyMemberProfile,
        conversation_id: Optional[str] = None
    ) -> ContentUpload:
        """Create database record for uploaded content."""

        # Calculate file metadata
        file_size = len(file_data)
        checksum_md5 = hashlib.md5(file_data).hexdigest()
        mime_type, _ = mimetypes.guess_type(filename)

        # Extract additional metadata based on content type
        metadata = await self._extract_metadata(file_data, content_type, filename)

        # Create upload record (this would be saved to database)
        upload = ContentUpload(
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=file_path,
            content_type=content_type,
            mime_type=mime_type,
            file_size_bytes=file_size,
            uploaded_by_id=family_member.user_id,  # This would be converted to UUID
            conversation_id=conversation_id,
            processing_status=ProcessingStatus.PENDING,
            privacy_level=family_member.photo_privacy_level if content_type == ContentType.IMAGE else family_member.voice_privacy_level,
            checksum_md5=checksum_md5,
            **metadata
        )

        # Save to database here (placeholder)
        # await db.add(upload)
        # await db.commit()

        return upload

    async def _extract_metadata(self, file_data: bytes, content_type: ContentType, filename: str) -> Dict[str, Any]:
        """Extract metadata from file data."""
        metadata = {}

        if content_type == ContentType.IMAGE:
            metadata = await self._extract_image_metadata(file_data)
        elif content_type == ContentType.AUDIO:
            metadata = await self._extract_audio_metadata(file_data, filename)
        elif content_type == ContentType.DOCUMENT:
            metadata = await self._extract_document_metadata(file_data, filename)

        return metadata

    async def _extract_image_metadata(self, file_data: bytes) -> Dict[str, Any]:
        """Extract metadata from image data."""
        try:
            with Image.open(io.BytesIO(file_data)) as img:
                # Auto-orient image based on EXIF
                img = ImageOps.exif_transpose(img)

                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format.lower() if img.format else 'unknown'
                }

                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        # Camera information, GPS, etc.
                        metadata['exif'] = str(exif)

                return metadata
        except Exception as e:
            raise ContentProcessorError(f"Failed to extract image metadata: {str(e)}")

    async def _extract_audio_metadata(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Extract metadata from audio data."""
        try:
            with tempfile.NamedTemporaryFile() as temp_file:
                await aiofiles.write(temp_file.name, file_data)
                audio = AudioSegment.from_file(temp_file.name)

                metadata = {
                    'duration_seconds': len(audio) / 1000.0,
                    'channels': audio.channels,
                    'frame_rate': audio.frame_rate,
                    'sample_width': audio.sample_width
                }

                # Get format information
                if hasattr(audio, 'format_info'):
                    metadata['format'] = audio.format_info.get('name', 'unknown')

                return metadata
        except Exception as e:
            raise ContentProcessorError(f"Failed to extract audio metadata: {str(e)}")

    async def _extract_document_metadata(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Extract metadata from document data."""
        try:
            extension = Path(filename).suffix.lower()
            metadata = {}

            if extension == '.pdf':
                import io
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                metadata.update({
                    'page_count': len(pdf_reader.pages),
                    'format': 'pdf'
                })
            elif extension == '.docx':
                # For DOCX files, we'd need to parse the document structure
                metadata.update({
                    'format': 'docx'
                })
            else:
                metadata.update({
                    'format': extension[1:] if extension else 'unknown'
                })

            return metadata
        except Exception as e:
            raise ContentProcessorError(f"Failed to extract document metadata: {str(e)}")

    async def _process_image(self, upload: ContentUpload) -> ContentProcessingResult:
        """Process image content with vision analysis."""
        import io

        # Update status
        upload.processing_status = ProcessingStatus.PROCESSING
        upload.processing_started_at = datetime.utcnow()

        try:
            # Read image file
            async with aiofiles.open(upload.file_path, 'rb') as f:
                image_data = await f.read()

            # Create ImageContent object
            image_content = ImageContent(
                file_path=upload.file_path,
                metadata=MediaMetadata(
                    file_name=upload.original_filename,
                    mime_type=upload.mime_type,
                    file_size_bytes=upload.file_size_bytes,
                    width=upload.width,
                    height=upload.height,
                    format=upload.format or 'unknown'
                )
            )

            # Perform vision analysis
            analysis_results = await self._analyze_image(image_data, upload)

            # Update upload record with results
            upload.processing_status = ProcessingStatus.COMPLETED
            upload.processing_completed_at = datetime.utcnow()
            upload.extracted_data = analysis_results
            upload.safety_score = analysis_results.get('safety_score', 1.0)

            return create_content_processing_result(upload)

        except Exception as e:
            upload.processing_status = ProcessingStatus.FAILED
            upload.processing_error = str(e)
            raise

    async def _process_audio(self, upload: ContentUpload) -> ContentProcessingResult:
        """Process audio content with speech recognition."""
        # Update status
        upload.processing_status = ProcessingStatus.PROCESSING
        upload.processing_started_at = datetime.utcnow()

        try:
            # Create AudioContent object
            audio_content = AudioContent(
                file_path=upload.file_path,
                metadata=MediaMetadata(
                    file_name=upload.original_filename,
                    mime_type=upload.mime_type,
                    file_size_bytes=upload.file_size_bytes,
                    duration_seconds=upload.duration_seconds,
                    format=upload.format or 'unknown'
                )
            )

            # Perform transcription
            transcription_results = await self._transcribe_audio(upload)

            # Update upload record with results
            upload.processing_status = ProcessingStatus.COMPLETED
            upload.processing_completed_at = datetime.utcnow()
            upload.extracted_data = transcription_results
            upload.safety_score = transcription_results.get('safety_score', 1.0)

            return create_content_processing_result(upload)

        except Exception as e:
            upload.processing_status = ProcessingStatus.FAILED
            upload.processing_error = str(e)
            raise

    async def _process_document(self, upload: ContentUpload) -> ContentProcessingResult:
        """Process document content with text extraction."""
        # Update status
        upload.processing_status = ProcessingStatus.PROCESSING
        upload.processing_started_at = datetime.utcnow()

        try:
            # Create DocumentContent object
            doc_content = DocumentContent(
                file_path=upload.file_path,
                metadata=MediaMetadata(
                    file_name=upload.original_filename,
                    mime_type=upload.mime_type,
                    file_size_bytes=upload.file_size_bytes,
                    format=upload.format or 'unknown'
                )
            )

            # Extract text
            extraction_results = await self._extract_document_text(upload)

            # Update upload record with results
            upload.processing_status = ProcessingStatus.COMPLETED
            upload.processing_completed_at = datetime.utcnow()
            upload.extracted_data = extraction_results
            upload.safety_score = extraction_results.get('safety_score', 1.0)

            return create_content_processing_result(upload)

        except Exception as e:
            upload.processing_status = ProcessingStatus.FAILED
            upload.processing_error = str(e)
            raise

    async def _process_generic_file(self, upload: ContentUpload) -> ContentProcessingResult:
        """Process generic file content."""
        # Update status
        upload.processing_status = ProcessingStatus.PROCESSING
        upload.processing_started_at = datetime.utcnow()

        try:
            # For generic files, just store metadata
            extraction_results = {
                'file_info': {
                    'filename': upload.original_filename,
                    'size': upload.file_size_bytes,
                    'mime_type': upload.mime_type,
                    'upload_time': upload.created_at.isoformat()
                }
            }

            # Update upload record
            upload.processing_status = ProcessingStatus.COMPLETED
            upload.processing_completed_at = datetime.utcnow()
            upload.extracted_data = extraction_results
            upload.safety_score = 1.0  # Default safe score for generic files

            return create_content_processing_result(upload)

        except Exception as e:
            upload.processing_status = ProcessingStatus.FAILED
            upload.processing_error = str(e)
            raise

    async def _analyze_image(self, image_data: bytes, upload: ContentUpload) -> Dict[str, Any]:
        """Analyze image using vision model."""
        try:
            # This would integrate with Ollama's vision model
            # For now, return mock analysis results

            # Convert image to base64 for API call
            import base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            # Mock vision analysis (replace with actual Ollama call)
            analysis = {
                'description': 'Image uploaded successfully',
                'objects_detected': [],
                'faces_detected': [],
                'text_detected': [],
                'emotional_analysis': {},
                'safety_score': 1.0,
                'processing_time_ms': 0.0
            }

            return analysis

        except Exception as e:
            raise ContentProcessorError(f"Vision analysis failed: {str(e)}")

    async def _transcribe_audio(self, upload: ContentUpload) -> Dict[str, Any]:
        """Transcribe audio using speech recognition."""
        try:
            # This would integrate with Whisper or other speech recognition
            # For now, return mock transcription

            transcription = {
                'transcription': 'Audio content processed successfully',
                'language_code': 'en',
                'speaker_count': 1,
                'confidence_score': 0.95,
                'keywords_spoken': [],
                'sentiment_analysis': {},
                'processing_time_ms': 0.0,
                'safety_score': 1.0
            }

            return transcription

        except Exception as e:
            raise ContentProcessorError(f"Audio transcription failed: {str(e)}")

    async def _extract_document_text(self, upload: ContentUpload) -> Dict[str, Any]:
        """Extract text from document."""
        try:
            import io
            text_content = ""

            async with aiofiles.open(upload.file_path, 'rb') as f:
                doc_data = await f.read()

            extension = Path(upload.original_filename).suffix.lower()

            if extension == '.pdf':
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(doc_data))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"

            elif extension == '.txt':
                text_content = doc_data.decode('utf-8')

            elif extension == '.md':
                text_content = doc_data.decode('utf-8')

            # For other formats, we'd need appropriate libraries

            extraction = {
                'extracted_text': text_content,
                'page_count': upload.page_count if hasattr(upload, 'page_count') else 1,
                'word_count': len(text_content.split()),
                'character_count': len(text_content),
                'summary': text_content[:500] + "..." if len(text_content) > 500 else text_content,
                'processing_time_ms': 0.0,
                'safety_score': 1.0
            }

            return extraction

        except Exception as e:
            raise ContentProcessorError(f"Document text extraction failed: {str(e)}")

    async def delete_content(self, upload_id: str) -> bool:
        """Delete uploaded content and its file."""
        try:
            # Get upload record from database
            # upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()

            # Delete file from storage
            # if upload and upload.file_path and os.path.exists(upload.file_path):
            #     os.remove(upload.file_path)

            # Delete database record
            # if upload:
            #     db.delete(upload)
            #     db.commit()

            return True

        except Exception as e:
            raise ContentProcessorError(f"Failed to delete content: {str(e)}")

    async def get_content_info(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get information about uploaded content."""
        try:
            # upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()

            # if upload:
            #     return {
            #         'id': str(upload.id),
            #         'original_filename': upload.original_filename,
            #         'content_type': upload.content_type.value,
            #         'file_size': upload.file_size_bytes,
            #         'upload_date': upload.created_at.isoformat(),
            #         'processing_status': upload.processing_status.value,
            #         'privacy_level': upload.privacy_level
            #     }

            return None

        except Exception as e:
            raise ContentProcessorError(f"Failed to get content info: {str(e)}")


# Global content processor instance
content_processor = ContentProcessor()