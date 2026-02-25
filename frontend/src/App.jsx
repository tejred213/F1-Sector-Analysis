import { Routes, Route } from 'react-router-dom';
import ComparePage from './pages/ComparePage';
import LandingPage from './pages/LandingPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/compare" element={<ComparePage />} />
    </Routes>
  );
}

export default App;
