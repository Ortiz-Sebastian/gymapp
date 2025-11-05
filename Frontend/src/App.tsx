import Navbar from './components/Navbar';
import HomePage from './components/HomePage';
import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-gray-50" style={{ margin: 0, padding: 0 }}>
      <Navbar />
      <HomePage />
    </div>
  );
}

export default App
