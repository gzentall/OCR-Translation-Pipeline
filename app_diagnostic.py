#!/usr/bin/env python3
"""
DIAGNOSTIC VERSION - User Deletion Endpoint
Replace the delete_user function temporarily to diagnose the production issue.
"""

from sqlalchemy import text
from flask import jsonify, session, request
from scripts.database import DatabaseSession, engine
from functools import wraps

# Use your existing require_role decorator
def require_role(min_role='Viewer'):
    """Your existing decorator"""
    pass  # Use the one from app.py

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_role('Admin')
def delete_user_diagnostic(user_id):
    """
    DIAGNOSTIC VERSION - Proves exactly where writes go and why they might "disappear"
    
    This version:
    1. Logs exact DB, role, schema, transaction ID, and read-only state
    2. Uses raw SQL UPDATE...RETURNING (bypasses ORM)
    3. Verifies with a brand-new connection
    4. Shows rowcount (0 means DB didn't update anything)
    """
    try:
        print("\n" + "="*80)
        print(f"[DIAGNOSTIC DELETE] Starting for user_id: {user_id}")
        print(f"[DIAGNOSTIC DELETE] Request user: {session.get('user_id')}, role: {session.get('role')}")
        print("="*80)
        
        with DatabaseSession() as db:
            # 1) PROVE CONNECTION IDENTITY & TRANSACTION STATE
            print("\n[STEP 1] Checking database connection details...")
            info = db.execute(text("""
                SELECT
                  current_database()             AS db,
                  current_user                   AS role,
                  current_schema                 AS schema,
                  current_setting('transaction_read_only', true) AS ro,
                  txid_current()                 AS txid
            """)).mappings().first()
            
            print(f"[DB INFO] Database: {info['db']}")
            print(f"[DB INFO] Role: {info['role']}")
            print(f"[DB INFO] Schema: {info['schema']}")
            print(f"[DB INFO] Read-only: {info['ro']}")
            print(f"[DB INFO] Transaction ID: {info['txid']}")
            
            if info['ro'] == 'on':
                print("⚠️  WARNING: Connection is READ-ONLY!")
                return jsonify({
                    "success": False, 
                    "error": "Database connection is read-only",
                    "diagnostic": dict(info)
                }), 500

            # 2) LOCK & VERIFY TARGET EXISTS
            print(f"\n[STEP 2] Looking up user {user_id} with FOR UPDATE lock...")
            target = db.execute(
                text("SELECT id, email, is_active FROM users WHERE id=:id FOR UPDATE"),
                {"id": user_id}
            ).mappings().first()
            
            if not target:
                print(f"❌ User {user_id} not found in database")
                return jsonify({"success": False, "error": "User not found"}), 404
            
            print(f"✅ Found user: {target['email']}, is_active={target['is_active']}")
            
            if user_id == session.get('user_id'):
                print("❌ Self-deletion attempt blocked")
                return jsonify({"success": False, "error": "Cannot delete your own account"}), 400

            # 3) PERFORM UPDATE AT SQL LEVEL (AUTHORITATIVE)
            print(f"\n[STEP 3] Executing SQL UPDATE on user {user_id}...")
            res = db.execute(
                text("""
                    UPDATE users
                       SET is_active = FALSE,
                           updated_at = NOW()
                     WHERE id = :id
                     RETURNING id, email, is_active, updated_at
                """),
                {"id": user_id}
            )
            row = res.mappings().first()
            rowcount = res.rowcount
            
            print(f"[UPDATE RESULT] rowcount={rowcount}")
            if row:
                print(f"[UPDATE RESULT] Returned row: id={row['id']}, email={row['email']}, is_active={row['is_active']}, updated_at={row['updated_at']}")
            else:
                print("⚠️  No row returned from UPDATE...RETURNING")

            if rowcount == 0:
                print("❌ UPDATE affected 0 rows - possible causes:")
                print("   - Row doesn't exist (unlikely, we just found it)")
                print("   - RLS policy blocking the update")
                print("   - Trigger preventing the update")
                print("   - Schema/table mismatch")
                return jsonify({
                    "success": False, 
                    "error": "Update affected 0 rows (possible RLS/trigger/schema mismatch)",
                    "diagnostic": {
                        "rowcount": 0,
                        "db": info['db'],
                        "schema": info['schema']
                    }
                }), 500

            print(f"\n[STEP 4] Committing transaction...")
            db.commit()
            print("✅ Transaction committed")

        # 4) RE-OPEN BRAND-NEW CONNECTION TO VERIFY
        print(f"\n[STEP 5] Opening NEW connection to verify what database actually has...")
        with DatabaseSession() as verify_db:
            verify = verify_db.execute(
                text("""
                    SELECT id, email, is_active, updated_at, 
                           current_database() AS db, 
                           current_schema AS schema 
                    FROM users 
                    WHERE id = :id
                """),
                {"id": user_id}
            ).mappings().first()
            
            if verify:
                print(f"[VERIFY] Database: {verify['db']}, Schema: {verify['schema']}")
                print(f"[VERIFY] User: {verify['email']}")
                print(f"[VERIFY] is_active: {verify['is_active']}")
                print(f"[VERIFY] updated_at: {verify['updated_at']}")
                
                if verify['is_active']:
                    print("❌ PROBLEM FOUND: User is still active after commit!")
                    print("   Likely causes:")
                    print("   - Database trigger reverting the change")
                    print("   - Another process re-activating the user")
                    print("   - Reading from a different database/replica")
                else:
                    print("✅ SUCCESS: User is correctly deactivated in database")
            else:
                print("⚠️  User not found in verification query")

        print("\n" + "="*80)
        print("[DIAGNOSTIC DELETE] Complete")
        print("="*80 + "\n")

        # 5) SURFACE RESULTS
        if not row:
            return jsonify({
                "success": False, 
                "error": "Update returned no rows",
                "diagnostic": {
                    "rowcount": rowcount,
                    "db": info['db'],
                    "schema": info['schema'],
                    "readonly": info['ro']
                }
            }), 500

        return jsonify({
            "success": True, 
            "message": "User deactivated successfully", 
            "diagnostic": {
                "rowcount": int(rowcount),
                "db": info['db'],
                "schema": info['schema'],
                "readonly": info['ro'],
                "verify": dict(verify) if verify else None
            }
        })
        
    except Exception as e:
        import traceback
        print("\n" + "="*80)
        print("[DIAGNOSTIC DELETE] ERROR")
        print("="*80)
        print(f"Error: {e}")
        print(traceback.format_exc())
        print("="*80 + "\n")
        return jsonify({"success": False, "error": str(e)}), 500

