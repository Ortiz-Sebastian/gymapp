import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './components/HomePage';
import GymDetailPage from './components/GymDetailPage';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import WriteReviewPage from './components/WriteReviewPage';
import MyReviewsPage from './components/MyReviewsPage';
import './App.css'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50" style={{ margin: 0, padding: 0 }}>
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/gym/:placeId" element={<GymDetailPage />} />
          <Route path="/gym/:placeId/review" element={<WriteReviewPage />} />
          <Route path="/gym/:placeId/review/edit/:reviewId" element={<WriteReviewPage />} />
          <Route path="/my-reviews" element={<MyReviewsPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App
