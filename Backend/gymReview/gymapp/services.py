import requests
import os
import logging
import math
import asyncio
import aiohttp
import h3
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from asgiref.sync import sync_to_async
from .models import Gym, TileCache
from django.db import connection
import json
from django.utils import timezone

logger = logging.getLogger(__name__)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points in miles using the Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in miles
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in miles
    r = 3959
    return c * r

# Async tiling functions for comprehensive gym discovery

def grid_centers(lat: float, lon: float, radius_m: int, tile_radius_m: int) -> List[Tuple[float, float]]:
    """Generate grid centers using H3 hexagonal grid with adaptive resolution"""
    # Choose H3 resolution based on search radius to avoid too many tiles
    radius_km = radius_m / 1000
    
    if radius_km <= 50:  # 50km or less
        h3_resolution = 8  # ~0.74km edge length
    elif radius_km <= 100:  # 100km or less  
        h3_resolution = 7  # ~1.5km edge length
    else:  # Larger than 100km
        h3_resolution = 6  # ~3km edge length
    
    # Get H3 hex containing the user location
    user_hex = h3.latlng_to_cell(lat, lon, h3_resolution)
    
    # Calculate how many hex rings we need to cover the radius
    # Use approximate hex diameter for each resolution
    hex_diameters = {5: 6.0, 6: 3.0, 7: 1.5, 8: 0.74}  # km
    hex_diameter_km = hex_diameters[h3_resolution]
    rings_needed = max(1, int(radius_km / hex_diameter_km) + 1)
    
    # Get all H3 hexes within the search radius
    hexes = h3.grid_disk(user_hex, rings_needed)
    
    # Convert H3 hexes back to lat/lon centers
    centers = []
    for hex_id in hexes:
        lat_center, lon_center = h3.cell_to_latlng(hex_id)
        centers.append((lat_center, lon_center))
    
    print(f"H3 grid generation: lat={lat:.6f}, lon={lon:.6f}, radius={radius_m}m")
    print(f"H3 resolution: {h3_resolution}, hex_diameter: {hex_diameter_km}km, rings: {rings_needed}")
    print(f"User hex: {user_hex}")
    print(f"Generated {len(centers)} H3 tile centers")
    print(f"First 3 hex centers: {centers[:3]}")
    
    return centers

async def fetch_pages(session: aiohttp.ClientSession, url: str, params: Dict) -> List[Dict]:
    """Fetch all pages for a single tile search"""
    out, seen = [], set()

    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        data = await resp.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        return out

    for it in data.get("results", []):
        pid = it.get("place_id")
        if pid and pid not in seen:
            seen.add(pid)
            out.append(it)

    next_token = data.get("next_page_token")
    page = 1
    while next_token and page < 3:
        await asyncio.sleep(1.5)  # Reduced delay for faster pagination
        async with session.get(url, params={"pagetoken": next_token, "key": params["key"]},
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
        if data.get("status") != "OK":
            break
        for it in data.get("results", []):
            pid = it.get("place_id")
            if pid and pid not in seen:
                seen.add(pid)
                out.append(it)
        next_token = data.get("next_page_token")
        page += 1

    return out

def split_tile(lat, lon, r_m):
    """Split a tile into 4 children for adaptive refinement"""
    # Use approximate conversion factors
    METERS_PER_DEG_LAT = 111_320.0
    meters_per_deg_lon = METERS_PER_DEG_LAT * math.cos(math.radians(lat))
    
    step = r_m * 0.8
    dlat = step / METERS_PER_DEG_LAT
    dlon = step / meters_per_deg_lon
    child_r = max(500, r_m // 2)   # 500 m lower bound keeps fanout sane
    return [
        (lat - dlat, lon - dlon, child_r),
        (lat - dlat, lon + dlon, child_r),
        (lat + dlat, lon - dlon, child_r),
        (lat + dlat, lon + dlon, child_r),
    ]

def sort_centers_by_distance(centers, lat0, lon0):
    """Sort tile centers by distance from user location (closest first)"""
    # Use approximate conversion factors
    METERS_PER_DEG_LAT = 111_320.0
    meters_per_deg_lon = METERS_PER_DEG_LAT * math.cos(math.radians(lat0))
    
    def d2(c):
        dy = (c[0] - lat0) * METERS_PER_DEG_LAT
        dx = (c[1] - lon0) * meters_per_deg_lon
        return dx * dx + dy * dy
    return sorted(centers, key=d2)

# Async wrappers for Django ORM calls - use database connection directly
async def async_get_cached(lat, lon, tile_r):
    """Get cached results using H3 hex ID as cache key with adaptive resolution"""
    # Choose H3 resolution based on tile radius (same logic as grid_centers)
    radius_km = tile_r / 1000
    
    if radius_km <= 50:  # 50km or less
        h3_resolution = 8  # ~0.74km edge length
    elif radius_km <= 100:  # 100km or less  
        h3_resolution = 7  # ~1.5km edge length
    else:  # Larger than 100km
        h3_resolution = 6  # ~3km edge length
    
    # Convert lat/lon to H3 hex ID for consistent caching
    hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
    key = f"{hex_id}|{tile_r}"
    # print(f"H3 cache lookup for key: {key}")  # Disabled for performance
    
    def get_cached_sync():
        import json
        with connection.cursor() as cursor:
            # Optimized query with single SELECT and conditional logic
            cursor.execute(
                "SELECT results_data, expires_at FROM gym_review_tile_cache WHERE cache_key = %s AND expires_at > NOW()",
                [key]
            )
            row = cursor.fetchone()
            if row:
                results_data_json, expires_at = row
                return json.loads(results_data_json)
            else:
                # Clean up expired entries in background
                cursor.execute("DELETE FROM gym_review_tile_cache WHERE cache_key = %s AND expires_at <= NOW()", [key])
                return None
    
    return await sync_to_async(get_cached_sync)()

async def async_set_cached(lat, lon, tile_r, results_data, ttl_days=7):
    """Cache results using H3 hex ID as cache key with adaptive resolution"""
    # Choose H3 resolution based on tile radius (same logic as grid_centers)
    radius_km = tile_r / 1000
    
    if radius_km <= 50:  # 50km or less
        h3_resolution = 8  # ~0.74km edge length
    elif radius_km <= 100:  # 100km or less  
        h3_resolution = 7  # ~1.5km edge length
    else:  # Larger than 100km
        h3_resolution = 6  # ~3km edge length
    
    # Convert lat/lon to H3 hex ID for consistent caching
    hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
    key = f"{hex_id}|{tile_r}"
    expires_at = timezone.now() + timezone.timedelta(days=ttl_days)
    # print(f"Setting H3 cache for key: {key} with {len(results_data)} results")  # Disabled for performance
    
    def set_cached_sync():
        import json
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO gym_review_tile_cache (cache_key, latitude, longitude, tile_radius, results_data, created_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cache_key) DO UPDATE SET
                    results_data = EXCLUDED.results_data,
                    expires_at = EXCLUDED.expires_at
            """, [key, lat, lon, tile_r, json.dumps(results_data), timezone.now(), expires_at])
            print(f"H3 cache {'created' if cursor.rowcount == 1 else 'updated'}: {key}")
    
    await sync_to_async(set_cached_sync)()

async def search_gyms_nearby_async(api_key: str, latitude: float, longitude: float, radius: int = 5000) -> List[Dict]:
    """Worker queue-based search with throttling and adaptive refinement"""
    print(f"=== SEARCH START ===")
    print(f"Input: lat={latitude:.6f}, lon={longitude:.6f}, radius={radius}m")
    base = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Choose tile radius based on search radius to ensure good coverage
    radius_km = radius / 1000
    if radius_km <= 10:  # 10km or less
        tile_radius_m = 1500  # 1.5km tiles (better coverage)
    elif radius_km <= 25:  # 25km or less  
        tile_radius_m = 2500  # 2.5km tiles (better coverage)
    elif radius_km <= 50:  # 50km or less
        tile_radius_m = 4000  # 4km tiles (better coverage)
    else:  # Larger than 50km
        tile_radius_m = 6000  # 6km tiles (better coverage)
    
    print(f"Using tile radius: {tile_radius_m}m for search radius: {radius}m")
    
    # In-memory cache for this request to avoid transaction isolation issues
    request_cache = {}
    cache_lock = asyncio.Lock()  # Thread-safe cache access
    
    # Batch cache writes for better performance
    cache_write_queue = []
    cache_write_lock = asyncio.Lock()
    
    # Concurrency and throttling controls
    SEM = asyncio.Semaphore(20)  # increased concurrency cap
    MIN_GAP = 0.02  # ~25 QPS throttle per process (faster)
    _last_call = 0.0
    
    async def throttled_get(session, url, params):
        """Throttled GET request to respect API rate limits"""
        nonlocal _last_call
        async with SEM:
            now = asyncio.get_event_loop().time()
            gap = MIN_GAP - (now - _last_call)
            if gap > 0:
                await asyncio.sleep(gap)
            async with session.get(url, params=params, timeout=15) as r:
                data = await r.json()
            _last_call = asyncio.get_event_loop().time()
            return data
    
    async def batch_cache_write():
        """Write all queued cache entries in a single batch"""
        if not cache_write_queue:
            return
        
        async with cache_write_lock:
            if not cache_write_queue:
                return
            
            # Process all queued writes
            batch = cache_write_queue.copy()
            cache_write_queue.clear()
            
            # Write all entries in a single transaction
            def batch_write_sync():
                import json
                with connection.cursor() as cursor:
                    for key, lat, lon, tile_r, results_data, expires_at in batch:
                        cursor.execute("""
                            INSERT INTO gym_review_tile_cache (cache_key, latitude, longitude, tile_radius, results_data, created_at, expires_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (cache_key) DO UPDATE SET
                                results_data = EXCLUDED.results_data,
                                expires_at = EXCLUDED.expires_at
                        """, [key, lat, lon, tile_r, json.dumps(results_data), timezone.now(), expires_at])
            
            await sync_to_async(batch_write_sync)()
            print(f"Batch wrote {len(batch)} cache entries")
    
    async def worker(name, queue, session, base, api_key, results_out):
        """Worker that processes tiles from the queue"""
        while True:
            item = await queue.get()
            if item is None:
                queue.task_done()
                return
            
            # Handle different item types
            if item[0] == "PAGINATE":
                # Handle pagination job
                _, tok, lat, lon, tile_r = item
                try:
                    await asyncio.sleep(1.5)  # Reduced delay for faster pagination
                    data = await throttled_get(session, base, {
                        "pagetoken": tok, 
                        "key": api_key
                    })
                    if data.get("status") == "OK":
                        out = data.get("results", [])
                        # Append to aggregate for this tile
                        h3_resolution = 8
                        hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
                        key = f"{hex_id}|{tile_r}"
                        async with aggregate_lock:
                            bucket = aggregate_results.get(key)
                            if bucket is None:
                                bucket = []
                                aggregate_results[key] = bucket
                            # Deduplicate by place_id while appending
                            existing_ids = {it.get("place_id") for it in bucket}
                            for it in out:
                                pid = it.get("place_id")
                                if pid and pid not in existing_ids:
                                    bucket.append(it)
                                    existing_ids.add(pid)
                        tok = data.get("next_page_token")
                        if tok:
                            # Enqueue next page if available
                            await queue.put(("PAGINATE", tok, lat, lon, tile_r))
                        else:
                            # Pagination complete, cache and add full aggregate to results (optimized)
                            h3_resolution = 8
                            hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
                            key = f"{hex_id}|{tile_r}"
                            async with aggregate_lock:
                                full = aggregate_results.pop(key, out)
                            # Store in in-memory cache first (faster)
                            async with cache_lock:
                                request_cache[key] = full
                            # Queue for batch cache write (much faster)
                            expires_at = timezone.now() + timezone.timedelta(days=7)
                            async with cache_write_lock:
                                cache_write_queue.append((key, lat, lon, tile_r, full, expires_at))
                            results_out.append((lat, lon, tile_r, full))
                    else:
                        results_out.append((lat, lon, tile_r, []))
                except Exception as e:
                    print(f"Worker {name} failed pagination for tile at ({lat:.4f}, {lon:.4f}): {e}")
                    results_out.append((lat, lon, tile_r, []))
            else:
                # Handle regular tile job
                lat, lon, tile_r = item
                try:
                    # Check in-memory cache first (same request)
                    # Use H3 hex ID as cache key
                    h3_resolution = 8
                    hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
                    cache_key = f"{hex_id}|{tile_r}"
                    print(f"Worker {name} checking cache for tile at ({lat:.6f}, {lon:.6f}) radius {tile_r}")
                    print(f"Checking cache for key: {cache_key}")
                    
                    # Check in-memory cache first (optimized)
                    cached_results = None
                    async with cache_lock:
                        if cache_key in request_cache:
                            cached_results = request_cache[cache_key]
                    
                    if cached_results is not None:
                        # Increment cached tiles counter
                        async with stats_lock:
                            tile_stats["cached"] += 1
                        # Process cached results
                        if len(cached_results) >= 60 and tile_r > 500:
                            # Split into 4 sub-tiles and add to queue
                            for sub_lat, sub_lon, sub_r in split_tile(lat, lon, tile_r):
                                await queue.put((sub_lat, sub_lon, sub_r))
                        else:
                            # Add cached results to output
                            results_out.append((lat, lon, tile_r, cached_results))
                        queue.task_done()
                        continue
                    
                    # Check database cache
                    cached_results = await async_get_cached(lat, lon, tile_r)
                    if cached_results:
                        # Store in in-memory cache for future use in this request (optimized)
                        async with cache_lock:
                            request_cache[cache_key] = cached_results
                        # Increment cached tiles counter
                        async with stats_lock:
                            tile_stats["cached"] += 1
                        # Process cached results
                        if len(cached_results) >= 60 and tile_r > 500:
                            # Split into 4 sub-tiles and add to queue
                            for sub_lat, sub_lon, sub_r in split_tile(lat, lon, tile_r):
                                await queue.put((sub_lat, sub_lon, sub_r))
                        else:
                            # Add cached results to output
                            results_out.append((lat, lon, tile_r, cached_results))
                        queue.task_done()
                        continue
                    else:
                        # Cache miss - fetch from API
                        print(f"Cache miss for tile at ({lat:.4f}, {lon:.4f}), fetching from API...")
                        # Increment fetched tiles counter once per tile when we miss cache
                        async with stats_lock:
                            tile_stats["fetched"] += 1
                        data = await throttled_get(session, base, {
                            "location": f"{lat},{lon}", 
                            "radius": tile_r, 
                            "type": "gym", 
                            "key": api_key
                        })
                        
                        out = data.get("results", [])
                        tok = data.get("next_page_token")
                        
                        if tok and len(out) == 20:
                            # Seed aggregate with first page and enqueue pagination
                            h3_resolution = 8
                            hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
                            key = f"{hex_id}|{tile_r}"
                            async with aggregate_lock:
                                # initialize with first page results (dedup)
                                seen = set()
                                first = []
                                for it in out:
                                    pid = it.get("place_id")
                                    if pid and pid not in seen:
                                        first.append(it)
                                        seen.add(pid)
                                aggregate_results[key] = first
                            # Let worker continue with other tiles
                            await queue.put(("PAGINATE", tok, lat, lon, tile_r))
                        else:
                            # No pagination needed, cache and process results
                            # Cache the results in both database and memory (optimized)
                            h3_resolution = 8
                            hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
                            cache_key = f"{hex_id}|{tile_r}"
                            # Store in in-memory cache first (faster)
                            async with cache_lock:
                                request_cache[cache_key] = out
                            # Queue for batch cache write (much faster)
                            expires_at = timezone.now() + timezone.timedelta(days=7)
                            async with cache_write_lock:
                                cache_write_queue.append((cache_key, lat, lon, tile_r, out, expires_at))
                            
                            # Check if tile needs refinement (saturated with 60+ results)
                            if len(out) >= 60 and tile_r > 500:
                                print(f"Tile at ({lat:.4f}, {lon:.4f}) saturated with {len(out)} results, refining...")
                                # Split into 4 sub-tiles and add to queue
                                for sub_lat, sub_lon, sub_r in split_tile(lat, lon, tile_r):
                                    await queue.put((sub_lat, sub_lon, sub_r))
                            else:
                                # Add results to output
                                results_out.append((lat, lon, tile_r, out))
                        
                except Exception as e:
                    print(f"Worker {name} failed to fetch tile at ({lat:.4f}, {lon:.4f}): {e}")
                    results_out.append((lat, lon, tile_r, []))  # Add empty result to maintain order
            
            queue.task_done()
    
    # Generate initial tiles using adaptive tile radius
    initial_centers = grid_centers(latitude, longitude, radius, tile_radius_m)
    print(f"Starting with {len(initial_centers)} tiles at {tile_radius_m}m radius")
    print(f"User location: lat={latitude:.6f}, lon={longitude:.6f}, radius={radius}m")
    print(f"First 3 tile centers: {initial_centers[:3]}")
    
    # Early termination: if we have too many tiles, use coarser resolution
    if len(initial_centers) > 1000:
        print(f"Too many tiles ({len(initial_centers)}), using coarser resolution...")
        # Use one resolution coarser
        radius_km = radius / 1000
        if radius_km <= 50:
            h3_resolution = 7  # coarser
        elif radius_km <= 100:
            h3_resolution = 6  # coarser
        else:
            h3_resolution = 5  # coarser
        
        user_hex = h3.latlng_to_cell(latitude, longitude, h3_resolution)
        hex_diameters = {5: 6.0, 6: 3.0, 7: 1.5, 8: 0.74}
        hex_diameter_km = hex_diameters[h3_resolution]
        rings_needed = max(1, int(radius_km / hex_diameter_km) + 1)
        hexes = h3.grid_disk(user_hex, rings_needed)
        
        initial_centers = []
        for hex_id in hexes:
            lat_center, lon_center = h3.cell_to_latlng(hex_id)
            initial_centers.append((lat_center, lon_center))
        
        print(f"Reduced to {len(initial_centers)} tiles with resolution {h3_resolution}")
    
    # Check for existing cached tiles from any radius
    print(f"Checking for existing cached tiles...")
    cached_tiles_found = 0
    
    def check_cached_tiles():
        count = 0
        for lat, lon in initial_centers[:5]:  # Check first 5 tiles
            # Check for tiles at this location with any radius
            try:
                entries = TileCache.objects.filter(
                    latitude__gte=lat-0.0001, latitude__lte=lat+0.0001,
                    longitude__gte=lon-0.0001, longitude__lte=lon+0.0001
                )
                for entry in entries:
                    if entry.is_fresh():
                        count += 1
                        print(f"Found cached tile: {entry.cache_key}")
                        break  # Only count one per location
            except Exception as e:
                print(f"Error checking cache for ({lat:.6f}, {lon:.6f}): {e}")
        return count
    
    cached_tiles_found = await sync_to_async(check_cached_tiles)()
    print(f"Found {cached_tiles_found} cached tiles out of {min(5, len(initial_centers))} checked")
    
    # Test cache with a simple tile
    test_lat, test_lon = initial_centers[0] if initial_centers else (latitude, longitude)
    print(f"Test coordinates: lat={test_lat} (type: {type(test_lat)}), lon={test_lon} (type: {type(test_lon)})")
    h3_resolution = 8
    test_hex_id = h3.latlng_to_cell(test_lat, test_lon, h3_resolution)
    test_cache_key = f"{test_hex_id}|{tile_radius_m}"
    print(f"Testing H3 cache with key: {test_cache_key}")
    test_cached = await async_get_cached(test_lat, test_lon, tile_radius_m)
    print(f"Test cache result: {'HIT' if test_cached else 'MISS'}")
    
    # Set up worker queue system
    results_out = []
    # Stats for debugging: track how many tiles were served from cache vs fetched
    tile_stats = {"cached": 0, "fetched": 0}
    stats_lock = asyncio.Lock()
    conn = aiohttp.TCPConnector(limit=32, ttl_dns_cache=300, keepalive_timeout=60)
    # Aggregate results per tile across pagination
    aggregate_results: Dict[str, List[Dict]] = {}
    aggregate_lock = asyncio.Lock()
    
    async with aiohttp.ClientSession(connector=conn) as session:
        q = asyncio.Queue()
        
        # Enqueue initial tiles (sorted by distance from user - closest first)
        centers_sorted = sort_centers_by_distance(initial_centers, latitude, longitude)
        for c in centers_sorted:
            await q.put((c[0], c[1], tile_radius_m))
        
        # Start workers
        workers = [
            asyncio.create_task(worker(f"W{i}", q, session, base, api_key, results_out)) 
            for i in range(20)  # increased worker count
        ]
        
        # Process all tiles
        await q.join()
        
        # Shutdown workers
        for _ in workers:
            await q.put(None)
        await asyncio.gather(*workers)
        
        # Write all queued cache entries in batch (much faster)
        await batch_cache_write()
    
    # Debug summary for tiling run
    try:
        total_processed = tile_stats["cached"] + tile_stats["fetched"]
        print(
            f"Tiling stats: cached tiles={tile_stats['cached']}, "
            f"fetched tiles={tile_stats['fetched']}, total processed={total_processed}"
        )
        # Check how many tiles are actually in the database
        def get_db_count():
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM gym_review_tile_cache")
                return cursor.fetchone()[0]
        
        db_count = await sync_to_async(get_db_count)()
        print(f"Total tiles in database cache: {db_count}")
    except Exception as e:
        print(f"Debug summary error: {e}")

    # Flatten and dedupe results
    seen, all_results = set(), []
    for lat, lon, tile_r, results in results_out:
        for it in results:
            pid = it.get("place_id")
            if pid and pid not in seen:
                seen.add(pid)
                all_results.append(it)
    
    # Trim back to original circle and filter gym types
    def haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dphi, dl = p2 - p1, math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return 2*R*math.asin(math.sqrt(a))
    
    def is_traditional_gym(place_data):
        """Filter to only include traditional gyms and fitness centers"""
        name = place_data.get("name", "").lower()
        types = place_data.get("types", [])
        
        # Exclude yoga studios, gymnastics, martial arts, dance studios, etc.
        exclude_keywords = [
            "yoga", "pilates", "barre", "dance", "martial arts", "karate", "taekwondo",
            "gymnastics", "gymnastic", "cheerleading", "ballet", "zumba", "spinning",
            "crossfit", "boxing", "kickboxing", "mma", "jiu jitsu", "aikido",
            "swimming", "pool", "aqua", "tennis", "racquet", "golf", "bowling",
            "archery", "shooting", "climbing", "rock climbing", "bouldering",
            "studio", "wellness", "spa", "massage", "physical therapy", "rehabilitation",
            "therapy", "rehab", "medical", "clinic", "center", "academy", "school"
        ]
        
        # Exclude specific Google Places types
        exclude_types = [
            "yoga_studio", "dance_school", "martial_arts_school", "gymnastics_center",
            "swimming_pool", "tennis_court", "golf_course", "bowling_alley",
            "climbing_gym", "rock_climbing_gym", "spa", "beauty_salon",
            "physical_therapy", "medical_clinic", "health_clinic"
        ]
        
        # Check if any excluded types are present
        if any(exclude_type in types for exclude_type in exclude_types):
            return False
        
        # Check if name contains excluded keywords
        for keyword in exclude_keywords:
            if keyword in name:
                return False
        
        # Include traditional gym types
        include_types = [
            "gym", "health", "fitness", "sports_complex", "establishment"
        ]
        
        # Check if any of the place types match our criteria
        return any(gym_type in types for gym_type in include_types)
    
    trimmed = []
    filtered_count = 0
    for it in all_results:
        # First filter by gym type
        if not is_traditional_gym(it):
            filtered_count += 1
            continue
            
        loc = it.get("geometry", {}).get("location", {})
        lat2, lon2 = loc.get("lat"), loc.get("lng")
        if lat2 is not None and lon2 is not None:
            if haversine_m(latitude, longitude, lat2, lon2) <= radius:
                trimmed.append(it)

    print(f"Filtered out {filtered_count} non-traditional gyms (yoga, martial arts, etc.)")
    print(f"=== SEARCH COMPLETE ===")
    print(f"User location: lat={latitude:.6f}, lon={longitude:.6f}, radius={radius}m ({radius/1609.34:.1f} miles)")
    print(f"Generated {len(initial_centers)} tiles")
    print(f"First 3 tile centers: {initial_centers[:3]}")
    print(f"Found {cached_tiles_found} cached tiles out of {min(5, len(initial_centers))} checked")
    print(f"Final stats: cached tiles={tile_stats['cached']}, fetched tiles={tile_stats['fetched']}")
    print(f"Total tiles in database cache: {db_count}")
    print(f"Found {len(trimmed)} traditional gyms using worker queue")
    return trimmed

class GooglePlacesService:
    def __init__(self):
        self.api_key = settings.GOOGLE_PLACES_API_KEY
        self.base_url = 'https://maps.googleapis.com/maps/api/place'
        
    def search_gyms_nearby(self, latitude: float, longitude: float, radius: int = 5000) -> List[Dict]:
        """
        Search for gyms near a location using async tiling for comprehensive coverage
        
        Args:
            latitude: Latitude of the search center
            longitude: Longitude of the search center
            radius: Search radius in meters (default: 5000m = ~3 miles)
            
        Returns:
            List of gym data from Google Places API within the specified radius
        """
        if not self.api_key:
            raise ValueError("Google Places API key not found. Set GOOGLE_PLACES_API_KEY environment variable.")
        
        print(f"Starting async tiling search for gyms within {radius}m radius...")
        
        # Run the async search with timeout
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Add timeout to prevent hanging
            results = loop.run_until_complete(
                asyncio.wait_for(
                    search_gyms_nearby_async(self.api_key, latitude, longitude, radius),
                    timeout=120  # 2 minute timeout
                )
            )
        except asyncio.TimeoutError:
            print("Search timed out after 2 minutes")
            results = []
        except Exception as e:
            print(f"Error in async search: {e}")
            results = []
        finally:
            loop.close()
        
        print(f"Raw API results before filtering: {len(results)}")
        
        # Convert radius from meters to miles for distance calculation
        radius_miles = radius * 0.000621371
        
        # Add distance information to results
        filtered_results = []
        for result in results:
            try:
                # Get gym coordinates
                gym_lat = result.get('geometry', {}).get('location', {}).get('lat')
                gym_lng = result.get('geometry', {}).get('location', {}).get('lng')
                
                if gym_lat and gym_lng:
                    # Calculate distance from user location to gym
                    distance = calculate_distance(latitude, longitude, gym_lat, gym_lng)
                    
                    # Add distance to the result for frontend use
                    result['distance_miles'] = round(distance, 2)
                    filtered_results.append(result)
                    
            except (TypeError, ValueError) as e:
                # Skip results with invalid coordinates
                continue
        
        # Sort by distance to ensure consistent ordering across requests
        filtered_results.sort(key=lambda x: x.get('distance_miles', float('inf')))
        
        print(f"Found {len(filtered_results)} gyms using async tiling search")
        print(f"Radius in miles: {radius_miles}")
                
        return filtered_results
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific place
        
        Args:
            place_id: Google Places place ID
            
        Returns:
            Detailed place information
        """
        if not self.api_key:
            raise ValueError("Google Places API key not found.")
        
        url = f"{self.base_url}/details/json"
        
        params = {
            'place_id': place_id,
            'fields': 'place_id,name,formatted_address,geometry,rating,user_ratings_total,formatted_phone_number,website,opening_hours,photos,types',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                return None
                
            return data.get('result')
            
        except requests.RequestException as e:
            raise Exception(f"Error calling Google Places API: {str(e)}")
    
    def create_or_update_gym(self, place_data: Dict) -> Gym:
        """
        Create or update a gym in the database from Google Places data
        
        Args:
            place_data: Place data from Google Places API
            
        Returns:
            Gym instance
        """
        place_id = place_data.get('place_id')
        
        # Get detailed information
        details = self.get_place_details(place_id)
        if not details:
            raise Exception(f"Could not get details for place {place_id}")
        
        # Extract coordinates
        geometry = details.get('geometry', {})
        location = geometry.get('location', {})
        latitude = location.get('lat')
        longitude = location.get('lng')
        
        # Extract photos - store all photo references
        photos = details.get('photos', [])
        photo_reference = photos[0].get('photo_reference') if photos else ''  # Legacy: first photo
        photo_references = [photo.get('photo_reference') for photo in photos if photo.get('photo_reference')]
        
        # Create or update gym
        gym, created = Gym.objects.get_or_create(
            place_id=place_id,
            defaults={
                'name': details.get('name', ''),
                'address': details.get('formatted_address', ''),
                'latitude': latitude,
                'longitude': longitude,
                'phone_number': details.get('formatted_phone_number', ''),
                'website': details.get('website', ''),
                'google_rating': details.get('rating'),
                'google_user_ratings_total': details.get('user_ratings_total'),
                'photo_reference': photo_reference,
                'photo_references': photo_references,  # Store all photo references
                'types': details.get('types', []),
                'opening_hours': details.get('opening_hours', {}),
            }
        )
        
        return gym


class GeocodingService:
    """
    Service for converting addresses, ZIP codes, and city/state to coordinates
    Supports multiple geocoding providers with fallbacks
    """
    
    def __init__(self):
        from django.conf import settings
        self.google_api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', os.getenv('GOOGLE_PLACES_API_KEY', ''))
        self.openstreetmap_enabled = True  # Free service, no API key needed
        
    def geocode_address(self, address: str) -> Dict:
        """
        Convert an address to coordinates
        
        Args:
            address: Full address string (e.g., "123 Main St, Los Angeles, CA 90210")
            
        Returns:
            Dict with latitude, longitude, formatted_address, and confidence
        """
        print(f"🔍 Geocoding address: '{address}'")
        print(f"🔍 Google API Key: {'Available' if self.google_api_key else 'Not available'}")
        
        # Try Google Geocoding first (most accurate)
        if self.google_api_key:
            try:
                print("🔍 Trying Google Geocoding API...")
                result = self._geocode_google(address)
                if result:
                    print(f"✅ Google geocoding successful: {result.get('formatted_address')}")
                    return result
                else:
                    print("⚠️  Google returned no results")
            except Exception as e:
                print(f"❌ Google geocoding failed: {e}")
                logger.warning(f"Google geocoding failed: {e}")
        else:
            print("⚠️  Skipping Google (no API key)")
        
        # Fallback to OpenStreetMap Nominatim (free)
        if self.openstreetmap_enabled:
            try:
                print("🔍 Trying OpenStreetMap Nominatim API...")
                result = self._geocode_openstreetmap(address)
                if result:
                    print(f"✅ OpenStreetMap geocoding successful: {result.get('formatted_address')}")
                    return result
                else:
                    print("⚠️  OpenStreetMap returned no results")
            except Exception as e:
                print(f"❌ OpenStreetMap geocoding failed: {e}")
                logger.warning(f"OpenStreetMap geocoding failed: {e}")
        
        error_msg = f"Could not find location: '{address}'. Please try a more specific address (include city and state)."
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    def geocode_zip_code(self, zip_code: str) -> Dict:
        """
        Convert a ZIP code to coordinates
        
        Args:
            zip_code: ZIP code string (e.g., "90210")
            
        Returns:
            Dict with latitude, longitude, and location info
        """
        # Try Google first
        if self.google_api_key:
            try:
                result = self._geocode_google(zip_code)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Google ZIP geocoding failed: {e}")
        
        # Fallback to OpenStreetMap
        if self.openstreetmap_enabled:
            try:
                result = self._geocode_openstreetmap(zip_code)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenStreetMap ZIP geocoding failed: {e}")
        
        raise ValueError(f"Could not geocode ZIP code: {zip_code}")
    
    def geocode_city_state(self, city: str, state: str) -> Dict:
        """
        Convert city and state to coordinates
        
        Args:
            city: City name (e.g., "Los Angeles")
            state: State name or abbreviation (e.g., "CA" or "California")
            
        Returns:
            Dict with latitude, longitude, and location info
        """
        address = f"{city}, {state}"
        return self.geocode_address(address)
    
    def _geocode_google(self, address: str) -> Optional[Dict]:
        """Geocode using Google Geocoding API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            'address': address,
            'key': self.google_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': result['formatted_address'],
                'confidence': self._calculate_google_confidence(result),
                'provider': 'google'
            }
        
        return None
    
    def _geocode_openstreetmap(self, address: str) -> Optional[Dict]:
        """Geocode using OpenStreetMap Nominatim API (free)"""
        url = "https://nominatim.openstreetmap.org/search"
        
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'GymReviewApp/1.0'  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            result = data[0]
            
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'formatted_address': result.get('display_name', address),
                'confidence': self._calculate_osm_confidence(result),
                'provider': 'openstreetmap'
            }
        
        return None
    
    def _calculate_google_confidence(self, result: Dict) -> float:
        """Calculate confidence score for Google geocoding result"""
        # Google provides accuracy levels in the geometry field
        location_type = result['geometry']['location_type']
        
        confidence_map = {
            'ROOFTOP': 1.0,
            'RANGE_INTERPOLATED': 0.8,
            'GEOMETRIC_CENTER': 0.6,
            'APPROXIMATE': 0.4
        }
        
        return confidence_map.get(location_type, 0.5)
    
    def _calculate_osm_confidence(self, result: Dict) -> float:
        """Calculate confidence score for OpenStreetMap result"""
        # OSM provides importance score (0-1, higher is better)
        importance = float(result.get('importance', 0.5))
        
        # Convert importance to confidence (0-1 scale)
        return min(importance * 1.2, 1.0)
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """
        Convert coordinates to address
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dict with formatted address and location details
        """
        # Try Google first
        if self.google_api_key:
            try:
                result = self._reverse_geocode_google(latitude, longitude)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Google reverse geocoding failed: {e}")
        
        # Fallback to OpenStreetMap
        if self.openstreetmap_enabled:
            try:
                result = self._reverse_geocode_openstreetmap(latitude, longitude)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenStreetMap reverse geocoding failed: {e}")
        
        raise ValueError(f"Could not reverse geocode coordinates: {latitude}, {longitude}")
    
    def _reverse_geocode_google(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Reverse geocode using Google Geocoding API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            'latlng': f"{latitude},{longitude}",
            'key': self.google_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            
            return {
                'formatted_address': result['formatted_address'],
                'address_components': result['address_components'],
                'provider': 'google'
            }
        
        return None
    
    def _reverse_geocode_openstreetmap(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Reverse geocode using OpenStreetMap Nominatim API"""
        url = "https://nominatim.openstreetmap.org/reverse"
        
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'GymReviewApp/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            return {
                'formatted_address': data.get('display_name', ''),
                'address_components': data.get('address', {}),
                'provider': 'openstreetmap'
            }
        
        return None


class LocationValidationService:
    """
    Service for validating and processing location data
    """
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """
        Validate that coordinates are within valid ranges
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        return (
            isinstance(latitude, (int, float)) and
            isinstance(longitude, (int, float)) and
            -90 <= latitude <= 90 and
            -180 <= longitude <= 180
        )
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lng1: First coordinate
            lat2, lng2: Second coordinate
            
        Returns:
            Distance in miles
        """
        import math
        
        # Earth's radius in miles
        R = 3959
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def is_within_radius(lat1: float, lng1: float, lat2: float, lng2: float, radius_miles: float) -> bool:
        """
        Check if two coordinates are within a specified radius
        
        Args:
            lat1, lng1: First coordinate
            lat2, lng2: Second coordinate
            radius_miles: Radius in miles
            
        Returns:
            True if within radius, False otherwise
        """
        distance = LocationValidationService.calculate_distance(lat1, lng1, lat2, lng2)
        return distance <= radius_miles


class ImageModerationService:
    """
    Service for moderating uploaded images to detect inappropriate content
    Supports multiple moderation providers with fallbacks
    """
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Moderation thresholds
        self.auto_approve_threshold = 0.8  # Auto-approve if confidence > 0.8
        self.auto_reject_threshold = 0.3   # Auto-reject if confidence < 0.3
        
        # Initialize AI detectors (lazy loading)
        self._nudenet_detector = None
        self._yolo_detector = None
        
    def moderate_image(self, image_path: str) -> Dict:
        """
        Moderate an uploaded image for inappropriate content
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with moderation results including confidence score and flags
        """
        try:
            # Try NudeNet first (local AI, fast and free)
            try:
                result = self._moderate_nudenet(image_path)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"NudeNet moderation failed: {e}")
            
            # Try Google Vision API as fallback
            if self.google_api_key:
                try:
                    result = self._moderate_google_vision(image_path)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Google Vision moderation failed: {e}")
            
            # Try AWS Rekognition as fallback
            if self.aws_access_key and self.aws_secret_key:
                try:
                    result = self._moderate_aws_rekognition(image_path)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"AWS Rekognition moderation failed: {e}")
            
            # Fallback to basic file analysis (very permissive)
            return self._basic_image_analysis(image_path)
            
        except Exception as e:
            logger.error(f"Image moderation failed: {e}")
            return {
                'confidence': 0.5,
                'flags': ['moderation_failed'],
                'provider': 'fallback',
                'safe': False  # Default to unsafe when moderation fails
            }
    
    def _moderate_nudenet(self, image_path: str) -> Optional[Dict]:
        """
        Moderate using NudeNet + YOLO (local AI models)
        - NudeNet: Detects nudity and NSFW content
        - YOLO: Detects weapons, drugs, and other inappropriate objects
        """
        try:
            from nudenet import NudeDetector
        except ImportError:
            logger.warning("NudeNet not installed, skipping local AI moderation")
            return None
        
        # Lazy load the detector (it's heavy, so only load once)
        if self._nudenet_detector is None:
            logger.info("Loading NudeNet detector model...")
            self._nudenet_detector = NudeDetector()
            logger.info("NudeNet detector loaded successfully")
        
        # Run NudeNet detection for NSFW content
        detections = self._nudenet_detector.detect(image_path)
        
        flags = []
        max_confidence = 0.0
        
        # === STEP 1: Check for NSFW content (nudity) ===
        nsfw_labels = {
            'EXPOSED_ANUS', 'EXPOSED_GENITALIA_F', 'EXPOSED_GENITALIA_M',
            'EXPOSED_BREAST_F', 'BUTTOCKS_EXPOSED'
        }
        
        racy_labels = {
            'EXPOSED_BUTTOCKS', 'COVERED_GENITALIA_F', 'COVERED_GENITALIA_M',
        }
        
        for detection in detections:
            label = detection.get('class', '')
            score = detection.get('score', 0.0)
            max_confidence = max(max_confidence, score)
            
            if label in nsfw_labels and score > 0.5:
                flags.append('nudity')
                logger.warning(f"NSFW content detected: {label} (score: {score:.2f})")
            elif label in racy_labels and score > 0.6:
                flags.append('racy')
                logger.info(f"Racy content detected: {label} (score: {score:.2f})")
        
        # === STEP 2: Check for inappropriate objects (weapons, drugs, etc.) ===
        object_flags, has_objects_detected = self._detect_inappropriate_objects(image_path)
        flags.extend(object_flags)
        
        # Determine overall confidence
        if flags:
            # Found inappropriate content, low confidence it's safe
            confidence = max(0.1, 1.0 - max_confidence) if max_confidence > 0 else 0.2
        else:
            # No inappropriate content detected, high confidence it's safe
            # Note: We don't require gym-related objects because legitimate gym photos
            # (locker rooms, walls, equipment close-ups, etc.) might not contain them
            confidence = 0.95
        
        return {
            'confidence': confidence,
            'flags': list(set(flags)),  # Remove duplicates
            'provider': 'nudenet+yolo',
            'safe': len(flags) == 0,
            'details': {
                'detections_count': len(detections),
                'max_detection_score': max_confidence
            }
        }
    
    def _detect_inappropriate_objects(self, image_path: str) -> tuple:
        """
        Detect inappropriate objects (weapons, drugs, etc.) using YOLOv8
        Returns tuple: (flags, has_objects_detected)
        - flags: list of inappropriate content flags
        - has_objects_detected: True if ANY objects were detected (image is readable)
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.warning("Ultralytics not installed, skipping object detection")
            return ([], True)  # Assume valid if detection unavailable
        
        flags = []
        has_objects_detected = False
        
        try:
            # Load YOLOv8 nano model (fast and efficient)
            # Model will auto-download on first use (~6MB)
            model = YOLO('yolov8n.pt')
            
            # Define inappropriate objects (COCO dataset classes)
            # Note: We're strict on weapons, lenient on bottles/cups
            # (since water bottles are common in gyms)
            inappropriate_objects = {
                'knife': 'inappropriate_objects',
                'scissors': 'inappropriate_objects',
            }
            
            # Run inference with verbose=False to reduce output
            results = model(image_path, verbose=False, conf=0.25)  # Lower confidence threshold
            
            # Process detections
            for result in results:
                if len(result.boxes) > 0:
                    has_objects_detected = True
                    logger.info(f"YOLOv8 detected {len(result.boxes)} objects in image")
                else:
                    logger.info(f"YOLOv8 detected no objects - image might be wall, floor, locker room, etc.")
                
                for box in result.boxes:
                    # Get class name and confidence
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # Debug: Log all detections
                    logger.info(f"  - Detected: {class_name} (confidence: {confidence:.2f})")
                    
                    # Check for inappropriate objects ONLY
                    if class_name in inappropriate_objects:
                        flag = inappropriate_objects[class_name]
                        flags.append(flag)
                        logger.warning(f"🚨 Inappropriate object detected: {class_name} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            # Don't fail the whole moderation if object detection fails
            return ([], True)
        
        return (flags, has_objects_detected)
    
    def _moderate_google_vision(self, image_path: str) -> Optional[Dict]:
        """Moderate using Google Vision API Safe Search"""
        import base64
        
        url = "https://vision.googleapis.com/v1/images:annotate"
        
        # Read and encode image
        with open(image_path, 'rb') as image_file:
            image_content = base64.b64encode(image_file.read()).decode('utf-8')
        
        payload = {
            "requests": [
                {
                    "image": {
                        "content": image_content
                    },
                    "features": [
                        {
                            "type": "SAFE_SEARCH_DETECTION"
                        },
                        {
                            "type": "OBJECT_LOCALIZATION"
                        }
                    ]
                }
            ]
        }
        
        params = {'key': self.google_api_key}
        
        response = requests.post(url, json=payload, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'responses' in data and data['responses']:
            response_data = data['responses'][0]
            
            if 'safeSearchAnnotation' in response_data:
                safe_search = response_data['safeSearchAnnotation']
                
                # Convert Google's likelihood to confidence score
                likelihood_map = {
                    'VERY_UNLIKELY': 0.1,
                    'UNLIKELY': 0.3,
                    'POSSIBLE': 0.5,
                    'LIKELY': 0.7,
                    'VERY_LIKELY': 0.9
                }
                
                flags = []
                max_confidence = 0.0
                
                # Check each category
                for category in ['adult', 'violence', 'racy']:
                    likelihood = safe_search.get(category, 'VERY_UNLIKELY')
                    confidence = likelihood_map.get(likelihood, 0.5)
                    max_confidence = max(max_confidence, confidence)
                    
                    if likelihood in ['LIKELY', 'VERY_LIKELY']:
                        flags.append(category)
                
                # Check for locker room/bathroom objects
                object_flags = self._check_for_inappropriate_objects(response_data.get('localizedObjectAnnotations', []))
                flags.extend(object_flags)
                
                return {
                    'confidence': max_confidence,
                    'flags': flags,
                    'provider': 'google_vision',
                    'safe': max_confidence < 0.5,
                    'details': safe_search
                }
        
        return None
    
    def _moderate_aws_rekognition(self, image_path: str) -> Optional[Dict]:
        """Moderate using AWS Rekognition"""
        try:
            import boto3
            
            client = boto3.client(
                'rekognition',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Detect inappropriate content
            response = client.detect_moderation_labels(
                Image={'Bytes': image_bytes},
                MinConfidence=50.0
            )
            
            flags = []
            max_confidence = 0.0
            
            for label in response.get('ModerationLabels', []):
                confidence = label['Confidence'] / 100.0  # Convert to 0-1 scale
                max_confidence = max(max_confidence, confidence)
                
                if confidence > 0.5:  # Only flag if confidence > 50%
                    flags.append(label['Name'].lower().replace(' ', '_'))
            
            return {
                'confidence': max_confidence,
                'flags': flags,
                'provider': 'aws_rekognition',
                'safe': max_confidence < 0.5,
                'details': response
            }
            
        except ImportError:
            logger.warning("boto3 not installed, skipping AWS Rekognition")
            return None
        except Exception as e:
            logger.warning(f"AWS Rekognition error: {e}")
            return None
    
    def _check_for_inappropriate_objects(self, objects: List[Dict]) -> List[str]:
        """Check for inappropriate objects in the image"""
        # Only flag objects that are inherently inappropriate, not bathroom facilities
        inappropriate_objects = [
            'weapon', 'gun', 'knife', 'drug', 'alcohol', 'cigarette',
            'explicit', 'adult_toy', 'condom'
        ]
        
        flags = []
        for obj in objects:
            object_name = obj.get('name', '').lower()
            if any(inappropriate in object_name for inappropriate in inappropriate_objects):
                flags.append('inappropriate_objects')
                break
        
        return flags
    
    def _basic_image_analysis(self, image_path: str) -> Dict:
        """Basic image analysis when AI services are unavailable"""
        try:
            from PIL import Image
            
            # Basic checks
            flags = []
            
            # Check file size (very large files might be suspicious)
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                flags.append('large_file')
            
            # Check image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Very small images might be thumbnails or low quality
                if width < 100 or height < 100:
                    flags.append('low_quality')
                
                # Very large images might be high resolution inappropriate content
                if width > 4000 or height > 4000:
                    flags.append('high_resolution')
            
            return {
                'confidence': 0.5,  # Neutral confidence for basic analysis
                'flags': flags,
                'provider': 'basic_analysis',
                'safe': len(flags) == 0,
                'details': {
                    'file_size': file_size,
                    'dimensions': {'width': width, 'height': height}
                }
            }
            
        except ImportError:
            logger.warning("PIL not installed, skipping basic image analysis")
            return {
                'confidence': 0.5,
                'flags': ['analysis_unavailable'],
                'provider': 'fallback',
                'safe': False
            }
        except Exception as e:
            logger.error(f"Basic image analysis failed: {e}")
            return {
                'confidence': 0.5,
                'flags': ['analysis_failed'],
                'provider': 'fallback',
                'safe': False
            }
    
    def determine_moderation_action(self, moderation_result: Dict) -> str:
        """
        Determine the moderation action based on the results
        
        Args:
            moderation_result: Result from moderate_image()
            
        Returns:
            'approved' or 'rejected' (fully automatic, no pending status)
        """
        confidence = moderation_result.get('confidence', 0.5)
        flags = moderation_result.get('flags', [])
        
        # Auto-reject for certain flags regardless of confidence
        auto_reject_flags = ['nudity', 'violence', 'inappropriate_objects', 'racy']
        if any(flag in auto_reject_flags for flag in flags):
            return 'rejected'
        
        # Auto-reject if very low confidence
        if confidence <= self.auto_reject_threshold:
            return 'rejected'
        
        # Auto-approve if high confidence and no concerning flags
        if confidence >= self.auto_approve_threshold and not flags:
            return 'approved'
        
        # For medium confidence (0.3 - 0.8), err on the side of approval
        # since it's better UX to approve borderline gym photos than reject them
        # Users can still report inappropriate photos later
        return 'approved'
    
    def get_rejection_reason(self, moderation_result: Dict) -> str:
        """Get the appropriate rejection reason based on moderation results"""
        flags = moderation_result.get('flags', [])
        
        if 'nudity' in flags or 'adult' in flags:
            return 'nudity'
        elif 'violence' in flags:
            return 'violence'
        elif 'inappropriate_objects' in flags:
            return 'inappropriate_content'
        elif 'spam' in flags:
            return 'spam'
        elif 'copyright' in flags:
            return 'copyright'
        else:
            return 'inappropriate_content'
