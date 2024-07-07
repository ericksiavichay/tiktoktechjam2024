import React, { useState, useEffect } from 'react';
import FrameSlider from './components/FrameSlider';
import FrameEditor from './components/FrameEditor';
import './App.css';

const LOCAL_HOST = process.env.REACT_APP_LOCAL_HOST;
const LOCAL_BACKEND_PORT = process.env.REACT_APP_LOCAL_BACKEND_PORT;

function App() {
  const [movies, setMovies] = useState([]);
  const [frames, setFrames] = useState([]);
  const [selectedFrame, setSelectedFrame] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [totalFrames, setTotalFrames] = useState(0);
  const [segmentedFrames, setSegmentedFrames] = useState([]);
  const [inpaintedVideo, setInpaintedVideo] = useState(null);

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
    setLoading(true);
    setLoadingMessage('Please wait, loading movie...');
    setSelectedMovie(movie);
    try {
      const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/movies/${movie}`);
      const data = await response.json();
      const totalFrames = data.total_frames;
      setTotalFrames(totalFrames);
      setFrames(data.frames || []);

      // Automatically select the first frame
      if (data.frames && data.frames.length > 0) {
        setSelectedFrame(data.frames[0]); // Set the first frame as selected
      }
    } catch (error) {
      console.error('Error loading movie frames:', error);
    }
    setLoading(false);
  };

  const handleSegmentVideo = async () => {
    setLoading(true);
    setLoadingMessage('Segmenting video...');
    try {
      const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/segment_video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keypoints: [], labels: [] }), // Update with actual keypoints and labels if necessary
      });
      const data = await response.json();
      setSegmentedFrames(data.segmented_frames || []);
    } catch (error) {
      console.error('Error segmenting video:', error);
    }
    setLoading(false);
  };

  const handleInpaintVideo = async () => {
    setLoading(true);
    setLoadingMessage('Inpainting video...');
    try {
      const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/inpaint_video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keypoints: [], labels: [] }), // Update with actual keypoints and labels if necessary
      });
      const data = await response.json();
      setInpaintedVideo(data.inpainted_video || null);
    } catch (error) {
      console.error('Error inpainting video:', error);
    }
    setLoading(false);
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
          onSelectFrame={() => { }} // Disable frame selection
          selectedFrameIndex={0} // Always keep the first frame selected
          totalFrames={totalFrames}
        />
      )}
      {!loading && selectedFrame && (
        <FrameEditor frame={selectedFrame} frameIndex={0} totalFrames={totalFrames} />
      )}
      {!loading && (
        <div className="video-buttons">
          <button onClick={handleSegmentVideo}>Segment Video</button>
          <button onClick={handleInpaintVideo}>Inpaint Video</button>
        </div>
      )}
      {!loading && segmentedFrames.length > 0 && (
        <FrameSlider
          frames={segmentedFrames}
          onSelectFrame={() => { }} // Disable frame selection
          selectedFrameIndex={0} // Always keep the first frame selected
          totalFrames={segmentedFrames.length}
        />
      )}
      {!loading && inpaintedVideo && (
        <div className="inpainted-video">
          <h2>Inpainted Video</h2>
          <video controls>
            <source src={`data:video/mp4;base64,${inpaintedVideo}`} type="video/mp4" />
          </video>
        </div>
      )}
    </div>
  );
}

export default App;
