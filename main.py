import blog_utils
from update_blog_data import parse_args, save_stats


def main():

    """Main function to update blog data"""
    args = parse_args()

    print("=== Blog Data Update ===")
    print(f"Data directory: {args.data_dir}")
    print(f"Force recreate: {args.force_recreate}")
    print("========================")

    # Process blog posts without creating embeddings
    try:
        # Load and process documents
        documents = blog_utils.load_blog_posts(args.data_dir)
        documents = blog_utils.update_document_metadata(documents)

        # Get stats
        stats = blog_utils.get_document_stats(documents)
        blog_utils.display_document_stats(stats)

        # Save stats for tracking
        stats_file = save_stats(stats)

        # Create a reference file for the vector store
        if args.force_recreate:
            print("\nAttempting to save vector store reference file...")
            blog_utils.create_vector_store(documents, force_recreate=args.force_recreate)

        print("\n=== Update Summary ===")
        print(f"Processed {stats['total_documents']} documents")
        print(f"Stats saved to: {stats_file}")
        print("Note: Vector store creation is currently disabled due to pickling issues.")
        print("      See VECTOR_STORE_ISSUES.md for more information and possible solutions.")
        print("=====================")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
