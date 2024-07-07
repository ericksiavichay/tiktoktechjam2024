import React, { useState, useEffect } from 'react';
import './FrameEditor.css';
import { FaStar } from 'react-icons/fa';

const REMOTE_HOST = process.env.REACT_APP_REMOTE_HOST;

function FrameEditor({ frame, setInitKeypoints, setInitLabels }) {
    const [keypoints, setKeypoints] = useState([]);
    const [labels, setLabels] = useState([]);
    const [selectedTool, setSelectedTool] = useState('positive');
    const [blendedFrame, setBlendedFrame] = useState(null);
    const [mask, setMask] = useState(null);
    const [inpaintedFrame, setInpaintedFrame] = useState(null);
    const [prompt, setPrompt] = useState('');
    const [negativePrompt, setNegativePrompt] = useState('');
    const [guidance, setGuidance] = useState(7.5);
    const [strength, setStrength] = useState(1.0);
    const [iterations, setIterations] = useState(50);
    const [originalDimensions, setOriginalDimensions] = useState({ width: 0, height: 0 });

    const handleImageLoad = (e) => {
        setOriginalDimensions({ width: e.target.naturalWidth, height: e.target.naturalHeight });
    };

    const handleMouseClick = (e) => {
        const img = e.target;
        const rect = img.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * originalDimensions.width;
        const y = ((e.clientY - rect.top) / rect.height) * originalDimensions.height;

        const newKeypoint = [x, y];
        const newLabel = selectedTool === 'positive' ? 1 : 0; // Use 1 for positive and 0 for negative

        setInitKeypoints([...keypoints, newKeypoint]);
        setInitLabels([...labels, newLabel]);

        setKeypoints([...keypoints, newKeypoint]);
        setLabels([...labels, newLabel]);
    };

    const handleClearKeypoints = () => {
        setKeypoints([]);
        setLabels([]);

        setInitKeypoints([]);
        setInitLabels([]);
    };

    const handleBackspace = (e) => {
        if (e.key === 'Backspace' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            setKeypoints(keypoints.slice(0, -1));
            setLabels(labels.slice(0, -1));

            setInitKeypoints(keypoints.slice(0, -1));
            setInitLabels(labels.slice(0, -1));
        }
    };

    useEffect(() => {
        document.addEventListener('keydown', handleBackspace);
        return () => {
            document.removeEventListener('keydown', handleBackspace);
        };
    }, [keypoints, labels]);

    const handleSegmentFrame = async () => {
        try {
            const response = await fetch(`${REMOTE_HOST}/segment_frame`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    frame,  // Ensure frame is a base64 encoded string
                    keypoints: keypoints, // Send keypoints as list of lists
                    labels: labels, // Send labels as is
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setBlendedFrame(data.blended_frame);
            setMask(data.mask);
        } catch (error) {
            console.error('Error segmenting frame:', error);
        }
    };

    const handleInpaintFrame = async () => {
        try {
            const response = await fetch(`${REMOTE_HOST}/inpaint_frame`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    frame,  // Ensure frame is a base64 encoded string
                    mask,
                    prompt,
                    negative_prompt: negativePrompt,
                    guidance: parseFloat(guidance),
                    strength: parseFloat(strength),
                    iterations: parseInt(iterations),
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setInpaintedFrame(data.inpainted_frame);
        } catch (error) {
            console.error('Error inpainting frame:', error);
        }
    };

    return (
        <div className="frame-editor">
            <h2>Selected Frame 1/1</h2>
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
            <div className="prompts">
                <div className="prompt">
                    <label htmlFor="prompt">Prompt</label>
                    <input
                        id="prompt"
                        type="text"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="negative-prompt">Negative Prompt</label>
                    <input
                        id="negative-prompt"
                        type="text"
                        value={negativePrompt}
                        onChange={(e) => setNegativePrompt(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="guidance">Guidance</label>
                    <input
                        id="guidance"
                        type="number"
                        value={guidance}
                        onChange={(e) => setGuidance(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="strength">Strength</label>
                    <input
                        id="strength"
                        type="number"
                        value={strength}
                        onChange={(e) => setStrength(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="iterations">Iterations</label>
                    <input
                        id="iterations"
                        type="number"
                        value={iterations}
                        onChange={(e) => setIterations(e.target.value)}
                    />
                </div>
                <button className="tool-button" onClick={handleInpaintFrame}>
                    Inpaint Frame
                </button>
            </div>
            <div className="images-container">
                <div className="selected-frame" onClick={handleMouseClick}>
                    <img src={`data:image/jpeg;base64,${frame}`} alt="Selected Frame" onLoad={handleImageLoad} />
                    {keypoints.map((kp, index) => (
                        <FaStar
                            key={index}
                            className="star-icon"
                            color={labels[index] === 1 ? 'green' : 'red'}
                            style={{ top: `${kp[1]}px`, left: `${kp[0]}px` }}
                        />
                    ))}
                </div>
                {blendedFrame && (
                    <div className="blended-frame">
                        <img src={`data:image/jpeg;base64,${blendedFrame}`} alt="Blended Frame" />
                    </div>
                )}
                {mask && (
                    <div className="mask-frame">
                        <img src={`data:image/png;base64,${mask}`} alt="Mask" />
                    </div>
                )}
                {inpaintedFrame && (
                    <div className="inpainted-frame">
                        <img src={`data:image/png;base64,${inpaintedFrame}`} alt="Inpainted Frame" />
                    </div>
                )}
            </div>
        </div>
    );
}

export default FrameEditor;
