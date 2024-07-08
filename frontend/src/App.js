import React, { useState, useEffect, lazy } from 'react';
import FrameSlider from './components/FrameSlider';
import FrameEditor from './components/FrameEditor';
import VideoPlayer from './components/VideoPlayer';
import './App.css';

const LOCAL_HOST = process.env.REACT_APP_LOCAL_HOST;
const LOCAL_BACKEND_PORT = process.env.REACT_APP_LOCAL_BACKEND_PORT;
const REMOTE_HOST = process.env.REACT_APP_REMOTE_HOST;

function App() {
  const [movies, setMovies] = useState([]);
  const [selectedFrame, setSelectedFrame] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [segURL, setSegURL] = useState(null);
  const [inpaintURL, setInpaintURL] = useState(null);

  useEffect(() => {
    const fetchMovies = async () => {
      try {
        const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/movies`);
        const data = await response.json();
        setMovies(data.movies || []);
      } catch (error) {
        console.error('Error fetching movies:', error);
      }
    };

    fetchMovies();
  }, []);

  const handleMovieSelect = async (movie) => {
    setSelectedMovie(movie);

    const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/movies/${movie}/thumbnail`);
    const data = await response.json();
    setSelectedFrame(data.thumbnail);
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

      {!loading && selectedMovie && (
        <VideoPlayer filename={selectedMovie} />
      )}

      {!loading && selectedFrame && (
        <FrameEditor frame={selectedFrame} videoURL={selectedMovie} setSegURL={setSegURL} />
      )}

      {!loading && segURL && (
        <VideoPlayer filename={segURL} />
      )}

      {!loading && inpaintURL && (
        <VideoPlayer filename={inpaintURL} />
      )}

    </div>
  );
}

export default App;
