import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface Gym {
  place_id: string;
  name: string;
  address: string;
}

const WriteReviewPage: React.FC = () => {
  const { placeId, reviewId } = useParams<{ placeId: string; reviewId?: string }>();
  const navigate = useNavigate();
  const [gym, setGym] = useState<Gym | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPhotos, setSelectedPhotos] = useState<File[]>([]);
  const [photoPreviewUrls, setPhotoPreviewUrls] = useState<string[]>([]);
  const [existingPhotos, setExistingPhotos] = useState<Array<{id: number; photo: string; caption: string}>>([]);
  const [photosToDelete, setPhotosToDelete] = useState<number[]>([]); // Track photos to delete
  const isEditMode = !!reviewId;

  const [formData, setFormData] = useState({
    equipment_rating: 0,
    cleanliness_rating: 0,
    staff_rating: 0,
    value_rating: 0,
    atmosphere_rating: 0,
    programs_classes_rating: 0,
    review_text: '',
    would_recommend: true,
    is_anonymous: false,
  });

  const [hoveredRatings, setHoveredRatings] = useState({
    equipment_rating: 0,
    cleanliness_rating: 0,
    staff_rating: 0,
    value_rating: 0,
    atmosphere_rating: 0,
    programs_classes_rating: 0,
  });

  const API_BASE_URL = 'http://localhost:8000/api';

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      // Redirect to login if not authenticated
      navigate('/login', { state: { from: `/gym/${placeId}/review` } });
      return;
    }

    if (placeId) {
      fetchGymDetails();
    }

    // If in edit mode, fetch the existing review
    if (isEditMode && reviewId) {
      fetchExistingReview();
    }
  }, [placeId, reviewId, navigate, isEditMode]);

  const fetchGymDetails = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/gyms/?place_id=${placeId}`);
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        setGym(data.results[0]);
      } else {
        setError('Gym not found');
      }
    } catch (err) {
      console.error('Error fetching gym details:', err);
      setError('Failed to load gym details');
    } finally {
      setLoading(false);
    }
  };

  const fetchExistingReview = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const review = await response.json();
        console.log('📥 Fetched existing review:', review);
        
        // Populate form with existing review data
        setFormData({
          equipment_rating: review.equipment_rating,
          cleanliness_rating: review.cleanliness_rating,
          staff_rating: review.staff_rating,
          value_rating: review.value_rating,
          atmosphere_rating: review.atmosphere_rating,
          programs_classes_rating: review.programs_classes_rating,
          review_text: review.review_text,
          would_recommend: review.would_recommend,
          is_anonymous: review.is_anonymous,
        });
        
        // Load existing photos if any
        if (review.photos && review.photos.length > 0) {
          console.log(`📸 Found ${review.photos.length} existing photos for review`);
          setExistingPhotos(review.photos.map((photo: any) => ({
            id: photo.id,
            photo: photo.photo,
            caption: photo.caption || ''
          })));
        }
      } else {
        setError('Failed to load review');
      }
    } catch (err) {
      console.error('Error fetching review:', err);
      setError('Failed to load review');
    }
  };

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Calculate total photos: existing (not deleted) + new
    const remainingExistingPhotos = existingPhotos.filter(p => !photosToDelete.includes(p.id)).length;
    const totalPhotos = remainingExistingPhotos + selectedPhotos.length + files.length;
    
    // Limit to 5 photos total
    if (totalPhotos > 5) {
      setError('You can have a maximum of 5 photos total (existing + new)');
      return;
    }
    
    // Validate file types and sizes
    const validFiles = files.filter(file => {
      const isValidType = file.type.startsWith('image/');
      const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB limit
      
      if (!isValidType) {
        setError(`${file.name} is not an image file`);
        return false;
      }
      if (!isValidSize) {
        setError(`${file.name} is too large (max 10MB)`);
        return false;
      }
      return true;
    });
    
    // Add valid files
    setSelectedPhotos(prev => [...prev, ...validFiles]);
    
    // Create preview URLs
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreviewUrls(prev => [...prev, reader.result as string]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removePhoto = (index: number) => {
    setSelectedPhotos(prev => prev.filter((_, i) => i !== index));
    setPhotoPreviewUrls(prev => prev.filter((_, i) => i !== index));
  };

  const removeExistingPhoto = (photoId: number) => {
    // Mark photo for deletion (will be deleted on submit)
    setPhotosToDelete(prev => [...prev, photoId]);
    // Remove from display
    setExistingPhotos(prev => prev.filter(p => p.id !== photoId));
  };

  const deletePhotos = async (token: string, photoIds: number[]) => {
    // Delete photos that were marked for removal
    const deletePromises = photoIds.map(async (photoId) => {
      try {
        const response = await fetch(`${API_BASE_URL}/photos/${photoId}/`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!response.ok) {
          console.error(`Failed to delete photo ${photoId}:`, response.status);
        } else {
          console.log(`✅ Photo ${photoId} deleted successfully`);
        }
      } catch (err) {
        console.error(`Error deleting photo ${photoId}:`, err);
      }
    });
    
    await Promise.all(deletePromises);
  };

  const uploadPhotos = async (token: string, reviewId: number) => {
    // Upload photos one by one and link them to the review
    const uploadPromises = selectedPhotos.map(async (photo) => {
      const formData = new FormData();
      formData.append('photo', photo);
      formData.append('gym', placeId!);
      formData.append('review', reviewId.toString()); // Link photo to review
      formData.append('caption', ''); // Optional caption
      
      try {
        const response = await fetch(`${API_BASE_URL}/photos/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error('Failed to upload photo:', photo.name, response.status, errorData);
        } else {
          const data = await response.json();
          console.log('✅ Photo uploaded successfully:', data);
        }
      } catch (err) {
        console.error('Error uploading photo:', err);
      }
    });
    
    await Promise.all(uploadPromises);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation: Ensure all ratings are provided
    if (
      formData.equipment_rating === 0 ||
      formData.cleanliness_rating === 0 ||
      formData.staff_rating === 0 ||
      formData.value_rating === 0 ||
      formData.atmosphere_rating === 0 ||
      formData.programs_classes_rating === 0
    ) {
      setError('Please provide ratings for all categories');
      return;
    }

    if (formData.review_text.trim().length < 10) {
      setError('Please write a review with at least 10 characters');
      return;
    }

    setSubmitting(true);

    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setError('You must be logged in to submit a review');
        setSubmitting(false);
        return;
      }

      // Submit the review with is_anonymous flag
      const url = isEditMode 
        ? `${API_BASE_URL}/reviews/${reviewId}/`
        : `${API_BASE_URL}/reviews/`;
      
      const method = isEditMode ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          gym: placeId,  // Backend expects 'gym' field with place_id value
          ...formData,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const reviewIdToUse = isEditMode ? reviewId : data.id;
        
        // Delete photos marked for removal (edit mode only)
        if (isEditMode && photosToDelete.length > 0) {
          console.log(`🗑️  Deleting ${photosToDelete.length} photos from review`);
          await deletePhotos(token, photosToDelete);
        }
        
        // Upload new photos if any were selected
        if (selectedPhotos.length > 0 && reviewIdToUse) {
          console.log(`📤 Uploading ${selectedPhotos.length} photos to review ${reviewIdToUse} (edit mode: ${isEditMode})`);
          await uploadPhotos(token, parseInt(reviewIdToUse));
          console.log('✅ All photos uploaded successfully');
        }
        
        // Small delay to ensure backend has processed everything
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Success! Navigate back to gym detail page
        navigate(`/gym/${placeId}`);
      } else {
        // Handle DRF ValidationError format - can be string, object, or array
        let errorMessage = 'Failed to submit review. Please try again.';
        let existingReviewId = null;
        
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.error) {
          errorMessage = typeof data.error === 'string' ? data.error : data.error[0] || errorMessage;
          existingReviewId = data.existing_review_id;
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : data.detail[0] || errorMessage;
        } else if (data.non_field_errors) {
          errorMessage = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors;
        }
        
        // Check if it's a duplicate review error
        if (errorMessage.includes('already posted a review') && (existingReviewId || data.existing_review_id)) {
          const reviewId = existingReviewId || data.existing_review_id;
          // Offer to edit the existing review
          const editReview = window.confirm(
            'You have already posted a review for this gym. Would you like to edit your existing review instead?'
          );
          
          if (editReview) {
            // Navigate to edit the existing review
            navigate(`/gym/${placeId}/review/edit/${reviewId}`);
          } else {
            setError(errorMessage);
          }
        } else {
          setError(errorMessage);
        }
      }
    } catch (err) {
      console.error('Error submitting review:', err);
      setError('An error occurred. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderRatingSelector = (
    category: keyof typeof formData,
    label: string,
    description: string
  ) => {
    const currentRating = formData[category] as number;
    const hoveredRating = hoveredRatings[category as keyof typeof hoveredRatings];
    const displayRating = hoveredRating || currentRating;

    return (
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          {label}
        </label>
        <p className="text-xs text-gray-500 mb-2">{description}</p>
        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setFormData({ ...formData, [category]: star })}
              onMouseEnter={() =>
                setHoveredRatings({ ...hoveredRatings, [category]: star })
              }
              onMouseLeave={() =>
                setHoveredRatings({ ...hoveredRatings, [category]: 0 })
              }
              className="focus:outline-none transition-transform hover:scale-110"
            >
              <svg
                className={`w-10 h-10 ${
                  star <= displayRating ? 'text-yellow-400' : 'text-gray-300'
                } transition-colors`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
          ))}
          <span className="ml-2 text-sm text-gray-600 font-medium">
            {currentRating > 0 ? `${currentRating}/5` : 'Not rated'}
          </span>
        </div>
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

  if (error && !gym) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">{error}</h2>
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
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => navigate(`/gym/${placeId}`)}
            className="flex items-center text-blue-600 hover:text-blue-700 mb-4"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to {gym?.name}
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditMode ? 'Edit Your Review' : 'Write a Review'}
          </h1>
          <p className="text-gray-600 mt-2">{gym?.name}</p>
          <p className="text-sm text-gray-500">{gym?.address}</p>
        </div>
      </div>

      {/* Review Form */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg shadow-md p-8">
          <form onSubmit={handleSubmit}>
            {/* Rating Categories */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Rate Your Experience</h2>
              
              {renderRatingSelector(
                'equipment_rating',
                'Equipment',
                'Quality, variety, and condition of gym equipment'
              )}
              
              {renderRatingSelector(
                'cleanliness_rating',
                'Cleanliness',
                'How clean and well-maintained is the facility'
              )}
              
              {renderRatingSelector(
                'staff_rating',
                'Staff',
                'Friendliness, helpfulness, and professionalism'
              )}
              
              {renderRatingSelector(
                'value_rating',
                'Value',
                'Price compared to quality and services offered'
              )}
              
              {renderRatingSelector(
                'atmosphere_rating',
                'Atmosphere',
                'Overall vibe, music, and environment'
              )}
              
              {renderRatingSelector(
                'programs_classes_rating',
                'Programs/Classes',
                'Quality and variety of classes and training programs'
              )}
            </div>

            {/* Photo Upload Section */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Add Photos (Optional)</h2>
              <p className="text-sm text-gray-600 mb-4">
                Help others by sharing photos of the gym. Maximum 5 photos, 10MB each.
              </p>
              
              {/* Photo Upload Button */}
              <label
                htmlFor="photo-upload"
                className="inline-flex items-center px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg cursor-pointer transition-colors"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                Choose Photos
              </label>
              <input
                id="photo-upload"
                type="file"
                accept="image/*"
                multiple
                onChange={handlePhotoSelect}
                className="hidden"
                disabled={(existingPhotos.filter(p => !photosToDelete.includes(p.id)).length + selectedPhotos.length) >= 5}
              />
              
              {/* Existing Photos (Edit Mode) */}
              {existingPhotos.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Current Photos</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    {existingPhotos.map((photo) => (
                      <div key={photo.id} className="relative group">
                        <img
                          src={photo.photo}
                          alt={photo.caption || 'Review photo'}
                          className="w-full h-24 object-cover rounded-lg border-2 border-gray-200"
                        />
                        {/* Remove Button */}
                        <button
                          type="button"
                          onClick={() => removeExistingPhoto(photo.id)}
                          className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity"
                          aria-label="Remove photo"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                        {photo.caption && (
                          <p className="text-xs text-gray-500 mt-1 truncate">{photo.caption}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* New Photo Previews */}
              {photoPreviewUrls.length > 0 && (
                <div className="mt-4">
                  {existingPhotos.length > 0 && <p className="text-sm font-medium text-gray-700 mb-2">New Photos</p>}
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    {photoPreviewUrls.map((url, index) => (
                      <div key={index} className="relative group">
                        <img
                          src={url}
                          alt={`Preview ${index + 1}`}
                          className="w-full h-24 object-cover rounded-lg border-2 border-blue-200"
                        />
                        {/* Remove Button */}
                        <button
                          type="button"
                          onClick={() => removePhoto(index)}
                          className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity"
                          aria-label="Remove photo"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                        {/* Photo info */}
                        <p className="text-xs text-gray-500 mt-1 truncate">
                          {selectedPhotos[index].name}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <p className="text-xs text-gray-500 mt-2">
                {existingPhotos.filter(p => !photosToDelete.includes(p.id)).length + selectedPhotos.length}/5 photos
                {selectedPhotos.length > 0 && ' • New photos will be reviewed before appearing publicly'}
              </p>
            </div>

            {/* Comment Section */}
            <div className="mb-6">
              <label htmlFor="review_text" className="block text-sm font-semibold text-gray-700 mb-2">
                Your Review
              </label>
              <p className="text-xs text-gray-500 mb-2">
                Share details about your experience to help others make informed decisions
              </p>
              <textarea
                id="review_text"
                rows={6}
                value={formData.review_text}
                onChange={(e) => setFormData({ ...formData, review_text: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="What did you like or dislike about this gym? What should others know?"
              />
              <p className="text-xs text-gray-500 mt-1">
                {formData.review_text.length} characters (minimum 10)
              </p>
            </div>

            {/* Anonymous Toggle */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <label htmlFor="anonymous-toggle" className="block text-sm font-semibold text-gray-700 mb-1">
                    Post Anonymously
                  </label>
                  <p className="text-xs text-gray-500">
                    Your review will be shown as "Anonymous" instead of your username
                  </p>
                </div>
                <button
                  type="button"
                  id="anonymous-toggle"
                  onClick={() => {
                    setFormData({ ...formData, is_anonymous: !formData.is_anonymous });
                  }}
                  className={`relative inline-flex h-7 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    formData.is_anonymous ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      formData.is_anonymous ? 'translate-x-7' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {submitting ? 'Submitting...' : 'Submit Review'}
              </button>
              <button
                type="button"
                onClick={() => navigate(`/gym/${placeId}`)}
                className="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default WriteReviewPage;

