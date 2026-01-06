
from database import supabase

def get_unit_file_counts_safe(course_id):
    """
    Safely calculates the number of files in each unit for a given course.
    Returns a dictionary: {unit_id: count}
    Failure mode: Returns empty dict (shows no counts, but doesn't crash app).
    """
    try:
        # 1. Fetch Units
        u_res = supabase.table("library_units").select("id").eq("course_id", course_id).execute()
        if not u_res.data:
            return {}
        
        unit_ids = [u['id'] for u in u_res.data]
        if not unit_ids:
            return {}

        # 2. Fetch Files (Metadata only: id, unit_id)
        # We fetch all files for these units to count them locally.
        # This is safer than complex SQL/RPC for now.
        f_res = supabase.table("library_files").select("id, unit_id").in_("unit_id", unit_ids).execute()
        
        counts = {}
        # Initialize 0 for all units
        for uid in unit_ids:
            counts[uid] = 0
            
        # Tally up
        for f in f_res.data:
            uid = f['unit_id']
            if uid in counts:
                counts[uid] += 1
        
        return counts

    except Exception as e:
        print(f"StatsHelper Error: {e}")
        return {}
