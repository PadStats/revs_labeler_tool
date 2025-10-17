#!/usr/bin/env python
"""View resolver failure statistics.

Usage:
    python -m admin_tools.resolver_stats                    # Summary stats
    python -m admin_tools.resolver_stats --list             # List all failing images
    python -m admin_tools.resolver_stats --top 20           # Top 20 images by failure count
"""

from __future__ import annotations

import argparse
from google.cloud import firestore  # type: ignore
from auth import _fs_client


def show_summary(db: firestore.Client) -> None:  # type: ignore[valid-type]
    """Show summary statistics of resolver failures."""
    # Get global stats from metadata collection
    metadata = db.collection("REVS_metadata").document("resolver_stats")
    stats_doc = metadata.get()
    
    print(f"\n📊 Resolver Failure Summary")
    print(f"{'='*60}")
    
    if stats_doc.exists:
        stats = stats_doc.to_dict()
        total_failures = stats.get("total_failures", 0)
        total_images = stats.get("total_images_affected", 0)
        last_failure = stats.get("last_failure")
        last_image = stats.get("last_failed_image_id", "N/A")
        
        print(f"Total resolver failures:     {total_failures:,}")
        print(f"Images affected:             {total_images:,}")
        if total_images > 0:
            print(f"Average failures per image:  {total_failures / total_images:.1f}")
        print(f"Last failure:                {last_failure}")
        print(f"Last failed image:           {last_image}")
    else:
        print("✅ No resolver failures recorded in metadata")
    
    print()
    
    # Get per-image details
    images = db.collection("REVS_images")
    failing_query = images.where("resolver_failure_count", ">", 0).limit(1)
    failing_docs = list(failing_query.stream())
    
    if failing_docs:
        # Find image with most failures
        max_query = images.order_by("resolver_failure_count", direction=firestore.Query.DESCENDING).limit(1)
        max_doc = list(max_query.stream())[0]
        max_data = max_doc.to_dict()
        max_count = max_data.get("resolver_failure_count", 0)
        
        print(f"Image with most failures:    {max_doc.id} ({max_count} failures)")
        print(f"Last error:                  {max_data.get('last_resolver_error', 'N/A')[:50]}...")
    
    print()


def list_failing_images(db: firestore.Client, limit: int = 100) -> None:  # type: ignore[valid-type]
    """List images with resolver failures."""
    images = db.collection("REVS_images")
    
    query = (
        images.where("resolver_failure_count", ">", 0)
        .order_by("resolver_failure_count", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    
    docs = list(query.stream())
    
    if not docs:
        print("✅ No resolver failures recorded")
        return
    
    print(f"\n🔴 Images with Resolver Failures (top {limit})")
    print(f"{'='*80}")
    print(f"{'Image ID':<40} {'Failures':>10} {'Last Error':<30}")
    print(f"{'-'*80}")
    
    for doc in docs:
        data = doc.to_dict()
        image_id = doc.id
        count = data.get("resolver_failure_count", 0)
        last_error = data.get("last_resolver_error", "N/A")
        # Truncate error message
        if len(last_error) > 30:
            last_error = last_error[:27] + "..."
        
        print(f"{image_id:<40} {count:>10} {last_error:<30}")
    
    print()


def clear_failure_counts(db: firestore.Client, image_id: str | None = None) -> None:  # type: ignore[valid-type]
    """Clear resolver failure counts (for testing or after fixing resolver)."""
    images = db.collection("REVS_images")
    
    if image_id:
        # Clear specific image
        images.document(image_id).update({
            "resolver_failure_count": firestore.DELETE_FIELD,
            "last_resolver_failure": firestore.DELETE_FIELD,
            "last_resolver_error": firestore.DELETE_FIELD,
        })
        print(f"✅ Cleared failure counts for image: {image_id}")
    else:
        # Clear all (use with caution!)
        print("⚠️  This will clear ALL resolver failure counts. Type 'yes' to confirm:")
        confirm = input("> ")
        if confirm.lower() != "yes":
            print("Cancelled")
            return
        
        failing_query = images.where("resolver_failure_count", ">", 0)
        docs = list(failing_query.stream())
        
        batch = db.batch()
        count = 0
        for doc in docs:
            batch.update(doc.reference, {
                "resolver_failure_count": firestore.DELETE_FIELD,
                "last_resolver_failure": firestore.DELETE_FIELD,
                "last_resolver_error": firestore.DELETE_FIELD,
            })
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = db.batch()
        
        if count % 400 != 0:
            batch.commit()
        
        print(f"✅ Cleared failure counts for {count} images")


def main() -> None:
    parser = argparse.ArgumentParser(description="View resolver failure statistics")
    parser.add_argument("--list", action="store_true", help="List all failing images")
    parser.add_argument("--top", type=int, metavar="N", help="Show top N failing images")
    parser.add_argument("--clear", nargs="?", const="ALL", metavar="IMAGE_ID", 
                       help="Clear failure counts (optionally for specific image)")
    
    args = parser.parse_args()
    
    db: firestore.Client = _fs_client()  # type: ignore[valid-type]
    
    if args.clear:
        if args.clear == "ALL":
            clear_failure_counts(db)
        else:
            clear_failure_counts(db, args.clear)
    elif args.list:
        list_failing_images(db, limit=1000)
    elif args.top:
        list_failing_images(db, limit=args.top)
    else:
        show_summary(db)


if __name__ == "__main__":
    main()

