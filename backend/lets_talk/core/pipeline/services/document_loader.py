"""
Document loading and content processing module.

This module handles loading blog posts from files, parsing frontmatter,
and preparing documents for further processing.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from langchain.schema.document import Document
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders.text import TextLoader

from lets_talk.shared.config import (
    BASE_URL,
    BLOG_BASE_URL,
    DATA_DIR,
    DATA_DIR_PATTERN,
    INDEX_ONLY_PUBLISHED_POSTS,
    WEB_URLS
)
from ..utils.common_utils import handle_exceptions, log_execution_time, merge_metadata

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Handles loading and initial processing of blog documents.
    """
    
    def __init__(
        self,
        data_dir: str = DATA_DIR,
        data_dir_pattern: str = DATA_DIR_PATTERN,
        blog_base_url: str = BLOG_BASE_URL,
        base_url: str = BASE_URL,
        web_urls: Optional[List[str]] = WEB_URLS,
        index_only_published_posts: bool = INDEX_ONLY_PUBLISHED_POSTS
    ):
        """
        Initialize the document loader.
        
        Args:
            data_dir: Directory containing blog posts
            data_dir_pattern: Pattern to match files in the directory
            blog_base_url: Base URL for blog posts
            base_url: Base URL for absolute links
            web_urls: List of web URLs to include
            index_only_published_posts: Whether to only index published posts
        """
        self.data_dir = data_dir
        self.blog_base_url = blog_base_url.rstrip('/') + '/'
        self.base_url = base_url
        self.index_only_published = index_only_published_posts
        self.data_dir_pattern = data_dir_pattern
        self.web_urls = web_urls if web_urls else []
    
    @handle_exceptions(default_return=[])
    @log_execution_time()
    def load_documents(
        self,
        recursive: bool = True,
        show_progress: bool = True
    ) -> List[Document]:
        """
        Load documents from the data directory.
        
        Args:
            glob_pattern: Pattern to match files
            recursive: Whether to search subdirectories
            show_progress: Whether to show progress bar
            
        Returns:
            List of loaded Document objects
        """
        logger.info(f"Loading documents from {self.data_dir}")
        
        text_loader = DirectoryLoader(
            self.data_dir,
            glob=self.data_dir_pattern,
            show_progress=show_progress,
            recursive=recursive,
            loader_cls=TextLoader
        )
        
        documents = text_loader.load()
        logger.info(f"Loaded {len(documents)} raw documents")
        
        # Process documents
        processed_documents = self._process_documents(documents)
        
        # Filter published documents if configured
        if self.index_only_published:
            processed_documents = self._filter_published_documents(processed_documents)
        
        logger.info(f"Processed {len(processed_documents)} documents")
        return processed_documents
    
    def _process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Process documents by updating metadata and parsing frontmatter.
        
        Args:
            documents: List of raw documents
            
        Returns:
            List of processed documents
        """
        processed_docs = []
        
        for doc in documents:
            try:
                # Update basic metadata
                self._update_document_metadata(doc)
                
                # Parse frontmatter
                self._parse_frontmatter(doc)
                
                processed_docs.append(doc)
                
            except Exception as e:
                logger.warning(f"Error processing document {doc.metadata.get('source', 'unknown')}: {e}")
                # Still include the document with basic metadata
                processed_docs.append(doc)
        
        return processed_docs
    
    def _update_document_metadata(self, doc: Document) -> None:
        """
        Update document metadata with URL and basic information.
        
        Args:
            doc: Document to update
        """
        # Create URL from source path
        url = doc.metadata["source"].replace(self.data_dir, self.blog_base_url)
        
        # Remove index.md suffix if present
        if url.endswith(self.data_dir_pattern):
            url = url[:-len(self.data_dir_pattern)]
        
        # Remove .md suffix if present
        if url.endswith(".md"):
            url = url[:-3]
        
        doc.metadata["url"] = url
        
        # Extract post slug from directory structure
        path_parts = Path(doc.metadata["source"]).parts
        if len(path_parts) > 1:
            doc.metadata["post_slug"] = path_parts[-2]
        
        # Add content length
        doc.metadata["content_length"] = len(doc.page_content)
    
    def _parse_frontmatter(self, doc: Document) -> None:
        """
        Parse frontmatter from document content and update metadata.
        
        Args:
            doc: Document to parse frontmatter for
        """
        try:
            frontmatter_data = self._extract_frontmatter(doc.page_content)
            
            # Set post title
            path_parts = Path(doc.metadata["source"]).parts
            default_title = path_parts[-2].replace("-", " ").title() if len(path_parts) > 1 else "Untitled"
            doc.metadata["post_title"] = frontmatter_data.get("title", default_title)
            
            # Handle media URLs
            self._process_media_urls(doc.metadata, frontmatter_data)
            
            # Add other frontmatter fields
            self._add_frontmatter_fields(doc.metadata, frontmatter_data)
            
        except Exception as e:
            logger.warning(f"Error parsing frontmatter for {doc.metadata.get('source', 'unknown')}: {e}")
            # Set default title if parsing fails
            path_parts = Path(doc.metadata["source"]).parts
            doc.metadata["post_title"] = path_parts[-2].replace("-", " ").title() if len(path_parts) > 1 else "Untitled"
    
    def _extract_frontmatter(self, content: str) -> Dict[str, str]:
        """
        Extract frontmatter data from document content.
        
        Args:
            content: Document content
            
        Returns:
            Dictionary of frontmatter data
        """
        frontmatter_data = {}

        import frontmatter
        # Parse frontmatter using the frontmatter library
        try:
            post = frontmatter.loads(content)
            frontmatter_data = post.metadata
        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {e}")
            frontmatter_data = {}
        # content_parts = content.split('---', 2)
        # if len(content_parts) >= 3:  # Valid frontmatter found
        #     frontmatter_text = content_parts[1]
        #     for line in frontmatter_text.strip().split('\n'):
        #         if ':' in line:
        #             key, value = line.split(':', 1)
        #             key = key.strip()
        #             value = value.strip().strip('"')
        #             frontmatter_data[key] = value
        
        return frontmatter_data #type: ignore[return-value]
    
    def _process_media_urls(self, metadata: Dict, frontmatter_data: Dict[str, str]) -> None:
        """
        Process media URLs (cover images, videos) and make them absolute.
        
        Args:
            metadata: Document metadata to update
            frontmatter_data: Parsed frontmatter data
        """
        base_url = self.base_url or self.blog_base_url
        
        def make_absolute_url(url: str) -> str:
            """Convert relative URLs to absolute ones."""
            if url and not (url.startswith("http://") or url.startswith("https://")):
                return f"{base_url.rstrip('/')}/{url.lstrip('/')}"
            return url
        
        # Handle cover image and video
        for media_type in ["coverImage", "coverVideo"]:
            metadata_key = media_type.replace("cover", "cover_").lower()
            if media_type in frontmatter_data:
                metadata[metadata_key] = make_absolute_url(frontmatter_data[media_type])

        if "youTubeVideoId" in frontmatter_data:
            # Convert YouTube video ID to embed URL
            video_id = frontmatter_data["youTubeVideoId"].strip()
            if video_id:
                metadata["cover_video"] = f"https://www.youtube.com/embed/{video_id}"
            else:
                metadata["cover_video"] = ""
        else:
            metadata["cover_video"] = ""
    
    def _add_frontmatter_fields(self, metadata: Dict, frontmatter_data: Dict) -> None:
        """
        Add additional frontmatter fields to metadata.
        
        Args:
            metadata: Document metadata to update
            frontmatter_data: Parsed frontmatter data
        """
        # Simple string fields
        string_fields = ["date", "description", "readingTime"]
        for field in string_fields:
            if field in frontmatter_data:
                value = frontmatter_data[field]
                if field == "readingTime":
                    metadata["reading_time"] = str(value) if value is not None else ""
                else:
                    metadata[field] = str(value) if value is not None else ""
        
        # Categories field (handle both list and string formats)
        if "categories" in frontmatter_data:
            categories_value = frontmatter_data["categories"]
            if isinstance(categories_value, list):
                metadata["categories"] = categories_value
            elif isinstance(categories_value, str):
                # Parse string format like '["AI", "Testing"]' or 'AI, Testing'
                categories = categories_value.strip('[]').replace('"', '').replace("'", '')
                metadata["categories"] = [c.strip() for c in categories.split(',') if c.strip()]
            else:
                metadata["categories"] = []
        
        # Published field (handle both boolean and string formats)
        if "published" in frontmatter_data:
            published_value = frontmatter_data["published"]
            if isinstance(published_value, bool):
                metadata["published"] = published_value
            elif isinstance(published_value, str):
                metadata["published"] = published_value.lower() == "true"
            else:
                metadata["published"] = True  # Default to published
    
    def _filter_published_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents to only include published ones if configured.
        
        Args:
            documents: List of documents to filter
            
        Returns:
            Filtered list of documents
        """
        if not self.index_only_published:
            return documents
        
        filtered_docs = []
        for doc in documents:
            if doc.metadata.get("published", True):  # Default to True if not specified
                filtered_docs.append(doc)
            else:
                logger.debug(f"Skipping unpublished document: {doc.metadata.get('post_title', 'unknown')}")
        
        logger.info(f"Filtered to {len(filtered_docs)} published documents from {len(documents)} total")
        return filtered_docs


class DocumentStats:
    """
    Utility class for analyzing document statistics.
    """
    
    @staticmethod
    def calculate_stats(documents: List[Document]) -> Dict:
        """
        Calculate statistics about the documents.
        
        Args:
            documents: List of documents to analyze
            
        Returns:
            Dictionary with statistics
        """
        if not documents:
            return {
                "total_documents": 0,
                "total_characters": 0,
                "min_length": 0,
                "max_length": 0,
                "avg_length": 0,
                "documents": []
            }
        
        lengths = [len(doc.page_content) for doc in documents]
        
        stats = {
            "total_documents": len(documents),
            "total_characters": sum(lengths),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "avg_length": sum(lengths) / len(documents),
        }
        
        # Create document info list
        doc_info = []
        for doc in documents:
            doc_info.append({
                "url": doc.metadata.get("url", ""),
                "source": doc.metadata.get("source", ""),
                "title": doc.metadata.get("post_title", ""),
                "text_length": doc.metadata.get("content_length", 0),
                "date": doc.metadata.get("date", ""),
                "categories": doc.metadata.get("categories", []),
                "description": doc.metadata.get("description", ""),
                "cover_image": doc.metadata.get("cover_image", ""),
                "cover_video": doc.metadata.get("cover_video", ""),
                "reading_time": doc.metadata.get("reading_time", ""),
                "published": doc.metadata.get("published", True),
                "post_slug": doc.metadata.get("post_slug", ""),
            })
        
        stats["documents"] = doc_info
        return stats
    
    @staticmethod
    def display_stats(stats: Dict) -> None:
        """
        Display document statistics in a readable format.
        
        Args:
            stats: Statistics dictionary from calculate_stats
        """
        logger.info(f"Document Statistics:")
        logger.info(f"  Total Documents: {stats['total_documents']}")
        logger.info(f"  Total Characters: {stats['total_characters']}")
        logger.info(f"  Min Length: {stats['min_length']} characters")
        logger.info(f"  Max Length: {stats['max_length']} characters")
        logger.info(f"  Average Length: {stats['avg_length']:.2f} characters")
        
        if stats["documents"]:
            logger.info("Document Details:")
            for doc in stats["documents"]:
                logger.info(f"  - {doc['title']} ({doc['text_length']} chars)")


# Convenience functions for backward compatibility
def load_blog_posts(
    data_dir: str = DATA_DIR,
    data_dir_pattern: str = DATA_DIR_PATTERN,
    blog_base_url: str = BLOG_BASE_URL,
    base_url: str = BASE_URL,
    web_urls: Optional[List[str]] = WEB_URLS,
    index_only_published_posts: bool = INDEX_ONLY_PUBLISHED_POSTS,
    recursive: bool = True,
    show_progress: bool = True
) -> List[Document]:
    """
    Load blog posts from the specified directory.
    
    Args:
        data_dir: Directory containing the blog posts
        data_dir_pattern: Pattern to match files
        blog_base_url: Base URL for blog posts
        base_url: Base URL for absolute links
        web_urls: List of web URLs to include
        index_only_published_posts: Whether to only index published posts
        recursive: Whether to search subdirectories
        show_progress: Whether to show a progress bar
        
    Returns:
        List of Document objects containing the blog posts
    """
    loader = DocumentLoader(data_dir=data_dir,data_dir_pattern=data_dir_pattern,
                            blog_base_url=blog_base_url, base_url=base_url,
                            web_urls=web_urls, index_only_published_posts=index_only_published_posts)
    return loader.load_documents(recursive, show_progress)


def get_document_stats(documents: List[Document]) -> Dict:
    """
    Get statistics about the documents.
    
    Args:
        documents: List of Document objects
        
    Returns:
        Dictionary with statistics
    """
    return DocumentStats.calculate_stats(documents)


def display_document_stats(stats: Dict) -> None:
    """
    Display document statistics in a readable format.
    
    Args:
        stats: Dictionary with statistics from get_document_stats
    """
    DocumentStats.display_stats(stats)
