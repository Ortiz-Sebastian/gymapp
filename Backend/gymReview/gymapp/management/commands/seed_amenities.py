from django.core.management.base import BaseCommand
from gymapp.models import AmenityCategory, Amenity


class Command(BaseCommand):
    help = 'Seed initial amenity categories and amenities'

    def handle(self, *args, **options):
        self.stdout.write('Seeding amenity data...')
        
        # Create categories
        categories_data = [
            {'name': 'Equipment', 'description': 'Exercise equipment and machines', 'icon': 'dumbbell', 'sort_order': 1},
            {'name': 'Facilities', 'description': 'Building facilities and amenities', 'icon': 'building', 'sort_order': 2},
            {'name': 'Services', 'description': 'Additional services offered', 'icon': 'concierge', 'sort_order': 3},
            {'name': 'Classes', 'description': 'Group fitness classes', 'icon': 'users', 'sort_order': 4},
            {'name': 'Accessibility', 'description': 'Accessibility features', 'icon': 'wheelchair', 'sort_order': 5},
        ]
        
        for cat_data in categories_data:
            category, created = AmenityCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
        
        # Get categories for amenities
        equipment_cat = AmenityCategory.objects.get(name='Equipment')
        facilities_cat = AmenityCategory.objects.get(name='Facilities')
        services_cat = AmenityCategory.objects.get(name='Services')
        classes_cat = AmenityCategory.objects.get(name='Classes')
        accessibility_cat = AmenityCategory.objects.get(name='Accessibility')
        
        # Create amenities
        amenities_data = [
            # Equipment
            {'name': 'Free Weights', 'category': equipment_cat, 'icon': 'dumbbell'},
            {'name': 'Treadmills', 'category': equipment_cat, 'icon': 'running'},
            {'name': 'Ellipticals', 'category': equipment_cat, 'icon': 'infinity'},
            {'name': 'StairMaster', 'category': equipment_cat, 'icon': 'stairs'},
            {'name': 'Rowing Machines', 'category': equipment_cat, 'icon': 'water'},
            {'name': 'Stationary Bikes', 'category': equipment_cat, 'icon': 'bicycle'},
            {'name': 'Spin Bikes', 'category': equipment_cat, 'icon': 'bicycle'},
            {'name': 'Assault Bike / Air Bike', 'category': equipment_cat, 'icon': 'wind'},
            {'name': 'SkiErg', 'category': equipment_cat, 'icon': 'snowflake'},
            {'name': 'Smith Machine', 'category': equipment_cat, 'icon': 'cogs'},
            {'name': 'Squat Racks', 'category': equipment_cat, 'icon': 'weight-hanging'},
            {'name': 'Bench Press Stations', 'category': equipment_cat, 'icon': 'weight'},
            {'name': 'Leg Press Machine', 'category': equipment_cat, 'icon': 'shoe-prints'},
            {'name': 'Hack Squat Machine', 'category': equipment_cat, 'icon': 'shoe-prints'},
            {'name': 'Chest Press Machine', 'category': equipment_cat, 'icon': 'dumbbell'},
            {'name': 'Lat Pulldown Machine', 'category': equipment_cat, 'icon': 'arrow-down'},
            {'name': 'Cable Crossover Machine', 'category': equipment_cat, 'icon': 'arrows-h'},
            {'name': 'Dip Bars', 'category': equipment_cat, 'icon': 'hand-rock'},
            {'name': 'Pull-Up Bars', 'category': equipment_cat, 'icon': 'hand-rock'},
            {'name': 'Leg Curl / Extension Machine', 'category': equipment_cat, 'icon': 'shoe-prints'},
            {'name': 'Glute Ham Developer (GHD)', 'category': equipment_cat, 'icon': 'running'},
            {'name': 'Power Racks', 'category': equipment_cat, 'icon': 'weight-hanging'},
            {'name': 'Smith Rack', 'category': equipment_cat, 'icon': 'cog'},
            {'name': 'Functional Training', 'category': equipment_cat, 'icon': 'dumbbell'},
            {'name': 'Olympic Lifting Platform', 'category': equipment_cat, 'icon': 'weight'},
            {'name': 'Cable Machines', 'category': equipment_cat, 'icon': 'cable'},
            {'name': 'Kettlebells', 'category': equipment_cat, 'icon': 'dumbbell'},
            {'name': 'Resistance Bands', 'category': equipment_cat, 'icon': 'band'},

            
            # Facilities
            {'name': 'Locker Rooms', 'category': facilities_cat, 'icon': 'lock'},
            {'name': 'Showers', 'category': facilities_cat, 'icon': 'shower'},
            {'name': 'Sauna', 'category': facilities_cat, 'icon': 'thermometer'},
            {'name': 'Steam Room', 'category': facilities_cat, 'icon': 'cloud'},
            {'name': 'Swimming Pool', 'category': facilities_cat, 'icon': 'swimming-pool'},
            {'name': 'Hot Tub', 'category': facilities_cat, 'icon': 'hot-tub'},
            {'name': 'Parking', 'category': facilities_cat, 'icon': 'parking'},
            {'name': 'Free WiFi', 'category': facilities_cat, 'icon': 'wifi'},
            {'name': 'Air Conditioning', 'category': facilities_cat, 'icon': 'snowflake'},
            {'name': 'Water Fountains', 'category': facilities_cat, 'icon': 'tint'},
            {'name': 'Vending Machines', 'category': facilities_cat, 'icon': 'vending-machine'},
            {'name': 'Pro Shop', 'category': facilities_cat, 'icon': 'store'},
            
            # Services
            {'name': 'Personal Training', 'category': services_cat, 'icon': 'user-tie'},
            {'name': 'Nutrition Counseling', 'category': services_cat, 'icon': 'apple-alt'},
            {'name': 'Massage Therapy', 'category': services_cat, 'icon': 'hands'},
            {'name': 'Physical Therapy', 'category': services_cat, 'icon': 'user-md'},
            {'name': 'Childcare', 'category': services_cat, 'icon': 'baby'},
            {'name': 'Towel Service', 'category': services_cat, 'icon': 'tshirt'},
            {'name': 'Laundry Service', 'category': services_cat, 'icon': 'tshirt'},
            {'name': 'Guest Passes', 'category': services_cat, 'icon': 'ticket-alt'},
            {'name': 'Equipment Rental', 'category': services_cat, 'icon': 'hand-holding'},
            
            # Classes
            {'name': 'Yoga', 'category': classes_cat, 'icon': 'om'},
            {'name': 'Pilates', 'category': classes_cat, 'icon': 'user'},
            {'name': 'Zumba', 'category': classes_cat, 'icon': 'music'},
            {'name': 'Spin Class', 'category': classes_cat, 'icon': 'bicycle'},
            {'name': 'HIIT', 'category': classes_cat, 'icon': 'fire'},
            {'name': 'CrossFit', 'category': classes_cat, 'icon': 'dumbbell'},
            {'name': 'Boxing', 'category': classes_cat, 'icon': 'fist-raised'},
            {'name': 'Martial Arts', 'category': classes_cat, 'icon': 'fist-raised'},
            {'name': 'Dance', 'category': classes_cat, 'icon': 'music'},
            {'name': 'Aqua Fitness', 'category': classes_cat, 'icon': 'swimming-pool'},
            
            # Accessibility
            {'name': 'Wheelchair Accessible', 'category': accessibility_cat, 'icon': 'wheelchair'},
            {'name': 'Elevator', 'category': accessibility_cat, 'icon': 'elevator'},
            {'name': 'Accessible Parking', 'category': accessibility_cat, 'icon': 'parking'},
            {'name': 'Accessible Showers', 'category': accessibility_cat, 'icon': 'shower'},
            {'name': 'Accessible Equipment', 'category': accessibility_cat, 'icon': 'wheelchair'},
        ]
        
        for amenity_data in amenities_data:
            amenity, created = Amenity.objects.get_or_create(
                name=amenity_data['name'],
                category=amenity_data['category'],
                defaults={
                    'icon': amenity_data['icon'],
                    'status': 'approved'  # Pre-approved amenities
                }
            )
            if created:
                self.stdout.write(f'Created amenity: {amenity.name}')
            else:
                self.stdout.write(f'Amenity already exists: {amenity.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded amenity data!')
        )
