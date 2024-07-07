import React, { useState } from 'react';
import './FrameSlider.css';

function FrameSlider({ frames, selectedFrameIndex, totalFrames }) {
    const [currentIndex, setCurrentIndex] = useState(0);

    const handleLeftClick = () => {
        if (currentIndex > 0) {
            setCurrentIndex(currentIndex - 1);
        }
    };

    const handleRightClick = () => {
        if (currentIndex < totalFrames - 10) {
            setCurrentIndex(currentIndex + 1);
        }
    };

    const displayedFrames = frames.slice(currentIndex, currentIndex + 10);

    return (
        <div className="frame-slider-container">
            <div className="frame-display">
                {displayedFrames.map((frame, index) => (
                    <div
                        key={index}
                        className={`frame-thumbnail ${selectedFrameIndex === currentIndex + index ? 'selected' : ''}`}
                    >
                        <img src={`data:image/jpeg;base64,${frame}`} alt={`Frame ${currentIndex + index + 1}`} />
                    </div>
                ))}
            </div>
            <div className="slider-controls">
                <button onClick={handleLeftClick}>Left</button>
                <input
                    type="range"
                    min="0"
                    max={totalFrames - 10}
                    value={currentIndex}
                    onChange={(e) => setCurrentIndex(parseInt(e.target.value, 10))}
                />
                <button onClick={handleRightClick}>Right</button>
            </div>
        </div>
    );
}

export default FrameSlider;
