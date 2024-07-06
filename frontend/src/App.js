import React, { useState, useEffect } from 'react';
import FrameSlider from './components/FrameSlider';
import FrameEditor from './components/FrameEditor';
import './App.css';

const LOCAL_HOST = process.env.REACT_APP_LOCAL_HOST;
const LOCAL_BACKEND_PORT = process.env.REACT_APP_LOCAL_BACKEND_PORT;
const REMOTE_HOST = process.env.REACT_APP_REMOTE_HOST;

function App() {
  const [movies, setMovies] = useState([]);
  const [frames, setFrames] = useState([]);
  const [selectedFrame, setSelectedFrame] = useState(null);
  const [selectedFrameIndex, setSelectedFrameIndex] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [totalFrames, setTotalFrames] = useState(0);

  useEffect(() => {
    const fetchMovies = async () => {
      try {
        const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/movies`);
        const data = await response.json();
        setMovies(data.movies);
      } catch (error) {
        console.error('Error fetching movies:', error);
      }
    };

    fetchMovies();
  }, []);

  const handleMovieSelect = async (movie) => {
    setLoading(true);
    setLoadingMessage('Please wait, loading movie...');
    setSelectedMovie(movie);
    try {
      const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/movies/${movie}`);
      const data = await response.json();
      const totalFrames = data.total_frames;
      setTotalFrames(totalFrames);
      setFrames(data.frames);

      // Automatically select the first frame
      if (data.frames.length > 0) {
        setSelectedFrame(data.frames[0]);
        setSelectedFrameIndex(0);
      }
    } catch (error) {
      console.error('Error loading movie frames:', error);
    }
    setLoading(false);
  };

  const handleFrameSelect = (frame, index) => {
    setSelectedFrame(frame);
    setSelectedFrameIndex(index);
  };

  return (
    <div className="App">
      <h1>Custom Filters</h1>
      {loading && <div className="loading">{loadingMessage}</div>}
      {!loading && (
        <div className="movie-selection">
          <h2>Select Movie for Editing</h2>
          <div className="movie-list">
            {movies.map((movie, index) => (
              <div
                key={index}
                className={`movie-item ${selectedMovie === movie ? 'selected' : ''}`}
                onClick={() => handleMovieSelect(movie)}
              >
                <p>{movie}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {!loading && frames.length > 0 && (
        <FrameSlider
          frames={frames}
          onSelectFrame={handleFrameSelect}
          selectedFrameIndex={selectedFrameIndex}
          totalFrames={totalFrames}
        />
      )}
      {!loading && selectedFrame && (
        <FrameEditor frame={selectedFrame} frameIndex={selectedFrameIndex} totalFrames={totalFrames} />
      )}
    </div>
  );
}

export default App;
