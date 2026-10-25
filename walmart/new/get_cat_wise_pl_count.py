import db_config as db
import pymysql








if __name__ == '__main__':
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Fetch pending rows
        query = f"""
            SELECT id, pl_url
            FROM {db.link_table}
            WHERE status = 'pending'
              AND subcategory_url IS NOT NULL
              AND subcategory_url != 'N/A'
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("No pending category found.")
            exit()
        for row in rows:
            row_id = row["id"]
            subcategory_url = row["subcategory_url"]
            title = row["title"]
            try:
                # cat_id = main_url.rstrip("/").split("/")[-1]
                cat_id = subcategory_url.rstrip("/").split("/")[-1].split("?")[0]
                print("=" * 80)
                print(f"Processing ID: {row_id}")
                print(f"URL: {subcategory_url}")
                print(f"CAT ID: {cat_id}")
                # Run scraper
                result = get_sub_category_links(main_url, str(cat_id))
                # If successful update status
                if result != 500:
                    update_query = f"""
                        UPDATE {db.input_table}
                        SET status = 'completed',
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (row_id,))
                    conn.commit()
                    print(f"ID {row_id} completed.")
                else:
                    fail_query = f"""
                        UPDATE {db.input_table}
                        SET status = 'failed',
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    cursor.execute(fail_query, (row_id,))
                    conn.commit()
                    print(f"ID {row_id} failed.")
            except Exception as e:
                print(f"Error processing ID {row_id}: {e}")
                fail_query = f"""
                    UPDATE {db.input_table}
                    SET status = 'failed',
                        updated_at = NOW()
                    WHERE id = %s
                """
                cursor.execute(fail_query, (row_id,))
                conn.commit()
    finally:
        cursor.close()
        conn.close()