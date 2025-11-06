import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface Amenity {
  id: number;
  amenity: {
    id: number;
    name: string;
    category: {
      id: number;
      name: string;
    };
  };
  confidence_score: number;
  is_verified: boolean;
}

interface GooglePhoto {
  photo_reference: string;
  photo_url: string;  // We'll construct this from the reference
}

interface Gym {
  place_id: string;  // Primary key - no separate 'id' field
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  phone_number?: string;
  website?: string;
  google_rating?: number;
  google_user_ratings_total?: number;
  average_overall_rating: number;
  average_equipment_rating?: number;
  average_cleanliness_rating?: number;
  average_staff_rating?: number;
  average_value_rating?: number;
  average_atmosphere_rating?: number;
  average_programs_classes_rating?: number;
  distance_miles?: number;
  amenities?: Amenity[];
  photo_references?: string[];  // Array of Google photo references
}

interface Review {
  id: number;
  user: {
    username: string;
  };
  overall_rating: number;
  equipment_rating: number;
  cleanliness_rating: number;
  staff_rating: number;
  value_rating: number;
  atmosphere_rating: number;
  programs_classes_rating: number;
  review_text: string;
  created_at: string;
  updated_at: string;
  helpful_votes: number;
  not_helpful_votes: number;
}

const GymDetailPage: React.FC = () => {
  const { placeId } = useParams<{ placeId: string }>();
  const navigate = useNavigate();
  const [gym, setGym] = useState<Gym | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [photos, setPhotos] = useState<GooglePhoto[]>([]);
  const [selectedPhotoIndex, setSelectedPhotoIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const [currentUsername, setCurrentUsername] = useState<string | null>(null);

  const API_BASE_URL = 'http://localhost:8000/api';
  // Photos are now proxied through the backend to avoid CORS issues and keep API key secure

  useEffect(() => {
    if (placeId) {
      fetchGymDetails();
      fetchReviews();
    }
    
    // Get current username from localStorage
    const username = localStorage.getItem('username');
    setCurrentUsername(username);
  }, [placeId]);

  // Debug: Log reviews state whenever it changes
  useEffect(() => {
    console.log('🔄 Reviews state updated:', reviews);
    console.log('📊 Reviews count:', reviews.length);
  }, [reviews]);

  const handleVote = async (reviewId: number, voteType: 'helpful' | 'not_helpful') => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Please log in to vote on reviews');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}/vote/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ vote_type: voteType }),
      });

      if (response.ok) {
        // Refresh reviews to get updated vote counts
        fetchReviews();
      } else {
        const data = await response.json();
        alert(data.error || 'Failed to vote');
      }
    } catch (err) {
      console.error('Error voting:', err);
      alert('An error occurred while voting');
    }
  };

  const handleDeleteReview = async (reviewId: number) => {
    if (!window.confirm('Are you sure you want to delete this review?')) {
      return;
    }

    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // Refresh reviews after deletion
        fetchReviews();
      } else {
        alert('Failed to delete review');
      }
    } catch (err) {
      console.error('Error deleting review:', err);
      alert('An error occurred while deleting the review');
    }
  };

  const fetchGymDetails = async () => {
    console.log('GymDetailPage: Fetching gym with place_id:', placeId);
    
    try {
      const response = await fetch(`${API_BASE_URL}/gyms/?place_id=${placeId}`);
      const data = await response.json();
      console.log('GymDetailPage: Received data:', data);
      
      if (data.results && data.results.length > 0) {
        const gymData = data.results[0];
        console.log('GymDetailPage: Setting gym:', gymData.name, gymData.place_id);
        console.log('🔑 Gym ID:', gymData.id);
        console.log('📦 Full gymData object:', gymData);
        setGym(gymData);
        
        // Convert Google photo references to photo URLs (using backend proxy to avoid CORS)
        if (gymData.photo_references && gymData.photo_references.length > 0) {
          console.log('📸 Found', gymData.photo_references.length, 'Google photo references');
          console.log('📸 First photo reference:', gymData.photo_references[0]);
          const googlePhotos = gymData.photo_references.map((reference: string) => {
            // Use backend proxy endpoint to avoid CORS issues
            const photoUrl = `${API_BASE_URL}/gyms/proxy_photo/?photo_reference=${reference}&maxwidth=800`;
            console.log('📸 Constructed proxy photo URL:', photoUrl.substring(0, 100) + '...');
            return {
              photo_reference: reference,
              photo_url: photoUrl
            };
          });
          setPhotos(googlePhotos);
          console.log('📸 Set photos state with', googlePhotos.length, 'photos');
        } else {
          console.log('📸 No photos available for this gym');
          setPhotos([]);
        }
      } else {
        setError('Gym not found');
      }
    } catch (err) {
      console.error('Error fetching gym details:', err);
      setError('Failed to load gym details');
    }
  };

  const fetchReviews = async () => {
    try {
      console.log('🔍 Fetching reviews for gym:', placeId);
      const response = await fetch(`${API_BASE_URL}/reviews/?gym=${placeId}`);
      console.log('📡 Reviews response status:', response.status);
      const data = await response.json();
      console.log('📦 Reviews data received:', data);
      const reviewsArray = data.results || data || [];
      console.log('✅ Setting reviews, count:', reviewsArray.length);
      setReviews(reviewsArray);
    } catch (err) {
      console.error('❌ Error fetching reviews:', err);
    } finally {
      setLoading(false);
    }
  };


  const renderStars = (rating: number | undefined | null, showNumber: boolean = true) => {
    const validRating = Number(rating) || 0;
    return (
      <div className="flex items-center">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-5 h-5 ${
              star <= validRating ? 'text-yellow-400' : 'text-gray-300'
            }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
        {showNumber && <span className="ml-2 text-sm text-gray-600">{validRating.toFixed(1)}</span>}
      </div>
    );
  };

  // Calculate rating distribution for a specific category
  const calculateRatingDistribution = (ratingField: keyof Review) => {
    const distribution = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    
    reviews.forEach(review => {
      const rating = Math.round(Number(review[ratingField]));
      if (rating >= 1 && rating <= 5) {
        distribution[rating as keyof typeof distribution]++;
      }
    });

    return distribution;
  };

  // Render rating distribution bars
  const renderRatingDistribution = (ratingField: keyof Review, categoryName: string) => {
    if (reviews.length === 0) return null;

    const distribution = calculateRatingDistribution(ratingField);
    const totalReviews = reviews.length;

    return (
      <div className="mt-2 space-y-1">
        {[5, 4, 3, 2, 1].map((stars) => {
          const count = distribution[stars as keyof typeof distribution];
          const percentage = totalReviews > 0 ? (count / totalReviews) * 100 : 0;

          return (
            <div key={stars} className="flex items-center gap-2 text-xs">
              <span className="text-gray-600 w-8">{stars}★</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-yellow-400 h-full transition-all duration-300"
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="text-gray-500 w-8 text-right">{count}</span>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !gym) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">{error || 'Gym not found'}</h2>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Search
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-blue-600 hover:text-blue-700 mb-4"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Search
          </button>
          <h1 className="text-3xl font-bold text-gray-900">{gym.name}</h1>
          <p className="text-gray-600 mt-2">{gym.address}</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Photo Carousel Section */}
        {photos.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">Photos ({currentPhotoIndex + 1} of {photos.length})</h2>
              <button className="text-blue-600 hover:text-blue-700 font-medium text-sm">
                Add Photo
              </button>
            </div>
            
            {/* Modern Stacked Carousel */}
            <div className="relative flex items-center justify-center" style={{ height: '500px' }}>
              {/* Stacked Cards Container */}
              <div className="relative w-full max-w-4xl" style={{ height: '450px', perspective: '1000px' }}>
                {photos.map((photo, index) => {
                  const offset = index - currentPhotoIndex;
                  const isActive = index === currentPhotoIndex;
                  const isPrev = offset === -1;
                  const isNext = offset === 1;
                  const isVisible = Math.abs(offset) <= 1;
                  
                  return (
                    <div
                      key={photo.photo_reference}
                      className="absolute inset-0 transition-all duration-500 ease-out cursor-pointer"
                      style={{
                        transform: `
                          translateX(${offset * 100}%)
                          translateZ(${isActive ? '0px' : '-100px'})
                          scale(${isActive ? 1 : 0.85})
                          rotateY(${offset * -5}deg)
                        `,
                        opacity: isVisible ? (isActive ? 1 : 0.4) : 0,
                        zIndex: isActive ? 20 : (isVisible ? 10 : 0),
                        pointerEvents: isActive ? 'auto' : 'none',
                      }}
                      onClick={() => isActive && setSelectedPhotoIndex(currentPhotoIndex)}
                    >
                      <div 
                        className="w-full h-full rounded-3xl overflow-hidden shadow-2xl"
                        style={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        }}
                      >
                        <img
                          src={photo.photo_url}
                          alt={`${gym?.name} photo ${index + 1}`}
                          className="w-full h-full"
                          style={{ 
                            objectFit: 'cover',
                          }}
                          onError={(e) => {
                            console.error('❌ Failed to load carousel image');
                          }}
                          onLoad={() => {
                            if (isActive) console.log('✅ Carousel image loaded');
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Navigation Arrows - Outside the cards */}
              {photos.length > 1 && (
                <>
                  {/* Previous Button */}
                  <button
                    onClick={() => setCurrentPhotoIndex(prev => prev === 0 ? photos.length - 1 : prev - 1)}
                    className="absolute left-0 top-1/2 -translate-y-1/2 bg-white hover:bg-gray-50 text-gray-700 p-4 rounded-full shadow-xl transition-all duration-200 hover:scale-110 hover:shadow-2xl z-30"
                    aria-label="Previous photo"
                  >
                    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>

                  {/* Next Button */}
                  <button
                    onClick={() => setCurrentPhotoIndex(prev => prev === photos.length - 1 ? 0 : prev + 1)}
                    className="absolute right-0 top-1/2 -translate-y-1/2 bg-white hover:bg-gray-50 text-gray-700 p-4 rounded-full shadow-xl transition-all duration-200 hover:scale-110 hover:shadow-2xl z-30"
                    aria-label="Next photo"
                  >
                    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </>
              )}
            </div>

            {/* Photo Indicator Dots */}
            {photos.length > 1 && (
              <div className="flex justify-center items-center space-x-2 mt-6">
                {photos.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentPhotoIndex(index)}
                    className={`transition-all duration-300 rounded-full ${
                      index === currentPhotoIndex 
                        ? 'w-8 h-3 bg-gradient-to-r from-purple-500 to-indigo-600' 
                        : 'w-3 h-3 bg-gray-300 hover:bg-gray-400'
                    }`}
                    aria-label={`Go to photo ${index + 1}`}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Photo Modal/Lightbox */}
        {selectedPhotoIndex !== null && (
          <div
            className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedPhotoIndex(null)}
          >
            <button
              className="absolute top-4 right-4 text-white hover:text-gray-300 text-4xl font-light"
              onClick={() => setSelectedPhotoIndex(null)}
            >
              ×
            </button>
            
            {/* Previous Button */}
            {selectedPhotoIndex > 0 && (
              <button
                className="absolute left-4 text-white hover:text-gray-300 text-4xl font-light"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPhotoIndex(selectedPhotoIndex - 1);
                }}
              >
                ‹
              </button>
            )}
            
            {/* Next Button */}
            {selectedPhotoIndex < photos.length - 1 && (
              <button
                className="absolute right-4 text-white hover:text-gray-300 text-4xl font-light"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPhotoIndex(selectedPhotoIndex + 1);
                }}
              >
                ›
              </button>
            )}

            <div className="max-w-5xl max-h-full" onClick={(e) => e.stopPropagation()}>
              <img
                src={photos[selectedPhotoIndex].photo_url}
                alt={`Photo ${selectedPhotoIndex + 1}`}
                className="max-w-full max-h-[80vh] object-contain mx-auto"
              />
              <p className="text-gray-400 text-center mt-2 text-sm">
                Photo {selectedPhotoIndex + 1} of {photos.length} • Source: Google Places
              </p>
            </div>
          </div>
        )}

        {/* Top Section: Overall Rating, Contact Info & Amenities */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Overall Rating */}
            <div className="lg:col-span-1">
              <h2 className="text-xl font-semibold mb-4">Overall Rating</h2>
              
              <div className="mb-4">
                <div className="flex items-center gap-4 mb-2">
                  <div className="text-5xl font-bold text-gray-900">
                    {(gym.average_overall_rating || 0).toFixed(1)}
                  </div>
                  <div className="text-3xl font-semibold text-gray-400">
                    / 5
                  </div>
                </div>
                {renderStars(gym.average_overall_rating)}
                {reviews.length > 0 && (
                  <p className="text-xs text-gray-500 mt-1">Based on {reviews.length} review{reviews.length !== 1 ? 's' : ''}</p>
                )}
              </div>
            </div>

            {/* Contact Info */}
            <div className="lg:col-span-1">
              <h2 className="text-xl font-semibold mb-4">Contact Information</h2>
              
              {gym.phone_number && (
                <div className="mb-3">
                  <p className="text-sm text-gray-500 mb-1">Phone</p>
                  <a href={`tel:${gym.phone_number}`} className="text-base text-blue-600 hover:underline">
                    {gym.phone_number}
                  </a>
                </div>
              )}

              {gym.website && (
                <div className="mb-3">
                  <p className="text-sm text-gray-500 mb-1">Website</p>
                  <a
                    href={gym.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-base text-blue-600 hover:underline break-all"
                  >
                    Visit Website
                  </a>
                </div>
              )}

              {!gym.phone_number && !gym.website && (
                <p className="text-sm text-gray-400">No contact information available</p>
              )}
            </div>

            {/* Amenities Section */}
            <div className="lg:col-span-1">
              <h2 className="text-xl font-semibold mb-4">Amenities</h2>
              {gym.amenities && gym.amenities.length > 0 ? (
                <div className="space-y-2">
                  {gym.amenities
                    .filter(a => a.is_verified)
                    .map((gymAmenity) => (
                      <div key={gymAmenity.id} className="flex items-center text-sm">
                        <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span className="text-gray-700">{gymAmenity.amenity.name}</span>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">No amenities listed</p>
              )}
            </div>
          </div>
        </div>

        {/* Detailed Category Ratings Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-6">Rating Breakdown</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Equipment */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">Equipment</p>
                <div className="flex items-center gap-2">
                  {renderStars(gym.average_equipment_rating, false)}
                  <span className="text-sm font-medium text-gray-600">
                    {(gym.average_equipment_rating || 0).toFixed(1)}
                  </span>
                </div>
              </div>
              {renderRatingDistribution('equipment_rating', 'Equipment')}
            </div>

            {/* Cleanliness */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">Cleanliness</p>
                <div className="flex items-center gap-2">
                  {renderStars(gym.average_cleanliness_rating, false)}
                  <span className="text-sm font-medium text-gray-600">
                    {(gym.average_cleanliness_rating || 0).toFixed(1)}
                  </span>
                </div>
              </div>
              {renderRatingDistribution('cleanliness_rating', 'Cleanliness')}
            </div>

            {/* Staff */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">Staff</p>
                <div className="flex items-center gap-2">
                  {renderStars(gym.average_staff_rating, false)}
                  <span className="text-sm font-medium text-gray-600">
                    {(gym.average_staff_rating || 0).toFixed(1)}
                  </span>
                </div>
              </div>
              {renderRatingDistribution('staff_rating', 'Staff')}
            </div>

            {/* Value */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">Value</p>
                <div className="flex items-center gap-2">
                  {renderStars(gym.average_value_rating, false)}
                  <span className="text-sm font-medium text-gray-600">
                    {(gym.average_value_rating || 0).toFixed(1)}
                  </span>
                </div>
              </div>
              {renderRatingDistribution('value_rating', 'Value')}
            </div>

            {/* Atmosphere */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">Atmosphere</p>
                <div className="flex items-center gap-2">
                  {renderStars(gym.average_atmosphere_rating, false)}
                  <span className="text-sm font-medium text-gray-600">
                    {(gym.average_atmosphere_rating || 0).toFixed(1)}
                  </span>
                </div>
              </div>
              {renderRatingDistribution('atmosphere_rating', 'Atmosphere')}
            </div>

            {/* Programs/Classes */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">Programs/Classes</p>
                <div className="flex items-center gap-2">
                  {renderStars(gym.average_programs_classes_rating, false)}
                  <span className="text-sm font-medium text-gray-600">
                    {(gym.average_programs_classes_rating || 0).toFixed(1)}
                  </span>
                </div>
              </div>
              {renderRatingDistribution('programs_classes_rating', 'Programs/Classes')}
            </div>
          </div>
        </div>

        {/* Reviews Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">
              Reviews ({reviews.length})
            </h2>
            <button
              onClick={() => {
                const token = localStorage.getItem('access_token');
                if (!token) {
                  // Redirect to login if not authenticated
                  navigate('/login', { state: { from: `/gym/${placeId}/review` } });
                } else {
                  // Navigate to write review page
                  navigate(`/gym/${placeId}/review`);
                }
              }}
              className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg"
            >
              Write a Review
            </button>
          </div>

          {reviews.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg mb-4">No reviews yet</p>
              <p className="text-gray-400">Be the first to review this gym!</p>
            </div>
          ) : (
            <div className="space-y-6">
              {reviews.map((review) => (
                <div key={review.id} className="border-b border-gray-200 pb-6 last:border-0">
                  {/* Review Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-semibold text-gray-900">{review.user.username}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(review.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                    </div>
                    {renderStars(review.overall_rating)}
                  </div>

                  {/* Review Text */}
                  <p className="text-gray-700 mb-4">{review.review_text}</p>

                  {/* Detailed Ratings */}
                  <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Equipment:</span>
                      <span className="font-medium">{review.equipment_rating}/5</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Cleanliness:</span>
                      <span className="font-medium">{review.cleanliness_rating}/5</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Staff:</span>
                      <span className="font-medium">{review.staff_rating}/5</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Value:</span>
                      <span className="font-medium">{review.value_rating}/5</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Atmosphere:</span>
                      <span className="font-medium">{review.atmosphere_rating}/5</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Programs/Classes:</span>
                      <span className="font-medium">{review.programs_classes_rating}/5</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    {/* Helpful/Not Helpful Buttons */}
                    <div className="flex items-center gap-4">
                      <button
                        onClick={() => handleVote(review.id, 'helpful')}
                        className="flex items-center gap-1 text-sm text-gray-600 hover:text-green-600 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                        </svg>
                        <span>Helpful ({review.helpful_votes})</span>
                      </button>
                      <button
                        onClick={() => handleVote(review.id, 'not_helpful')}
                        className="flex items-center gap-1 text-sm text-gray-600 hover:text-red-600 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                        </svg>
                        <span>Not Helpful ({review.not_helpful_votes})</span>
                      </button>
                    </div>

                    {/* Edit/Delete Buttons (only if user owns this review) */}
                    {currentUsername === review.user.username && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => navigate(`/gym/${placeId}/review/edit/${review.id}`)}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteReview(review.id)}
                          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GymDetailPage;

