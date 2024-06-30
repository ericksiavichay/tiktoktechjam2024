import React, { useState, useEffect } from 'react';
import './FrameEditor.css';
import { FaStar } from 'react-icons/fa';

const REMOTE_HOST = process.env.REACT_APP_REMOTE_HOST;

function FrameEditor({ frame, frameIndex, totalFrames }) {
    const [keypoints, setKeypoints] = useState([]);
    const [selectedTool, setSelectedTool] = useState('positive');
    const [segmentedFrame, setSegmentedFrame] = useState(null);

    const handleMouseClick = (e) => {
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const newKeypoint = {
            type: selectedTool,
            x,
            y,
        };

        setKeypoints([...keypoints, newKeypoint]);
    };

    const handleClearKeypoints = () => {
        setKeypoints([]);
    };

    const handleBackspace = (e) => {
        if (e.key === 'Backspace') {
            e.preventDefault();
            setKeypoints(keypoints.slice(0, -1));
        }
    };

    useEffect(() => {
        document.addEventListener('keydown', handleBackspace);
        return () => {
            document.removeEventListener('keydown', handleBackspace);
        };
    }, [keypoints]);

    const handleSegmentFrame = async () => {
        try {
            console.log('Sending request to:', `${REMOTE_HOST}/segment_frame`);
            const response = await fetch(`${REMOTE_HOST}/segment_frame`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    frame,  // Ensure frame is a base64 encoded string
                    keypoints: keypoints.map(kp => [kp.x, kp.y]),
                    labels: keypoints.map(kp => (kp.type === 'positive' ? 1 : 0)),
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setSegmentedFrame(data.segmented_frame);
        } catch (error) {
            console.error('Error segmenting frame:', error);
        }
    };

    return (
        <div className="frame-editor">
            <h2>Selected Frame {frameIndex + 1}/{totalFrames}</h2>
            <div className="tools">
                <button
                    className={`tool-button ${selectedTool === 'positive' ? 'selected' : ''}`}
                    onClick={() => setSelectedTool('positive')}
                >
                    <FaStar color="green" /> Positive Keypoint
                </button>
                <button
                    className={`tool-button ${selectedTool === 'negative' ? 'selected' : ''}`}
                    onClick={() => setSelectedTool('negative')}
                >
                    <FaStar color="red" /> Negative Keypoint
                </button>
                <button className="tool-button" onClick={handleClearKeypoints}>
                    Clear Keypoints
                </button>
                <button className="tool-button" onClick={handleSegmentFrame}>
                    Segment Frame
                </button>
            </div>
            <div className="selected-frame" onClick={handleMouseClick}>
                <img src={`data:image/jpeg;base64,${frame}`} alt="Selected Frame" />
                {keypoints.map((kp, index) => (
                    <FaStar
                        key={index}
                        color={kp.type === 'positive' ? 'green' : 'red'}
                        style={{ position: 'absolute', top: kp.y, left: kp.x, pointerEvents: 'none' }}
                    />
                ))}
            </div>
            {segmentedFrame && (
                <div className="segmented-frame">
                    <img src={`data:image/jpeg;base64,${segmentedFrame}`} alt="Segmented Frame" />
                </div>
            )}
        </div>
    );
}

export default FrameEditor;
