import React from 'react';
import './VideoPlayer.css';

const VideoPlayer = ({ filename }) => {
    const api = `http://localhost:5001/movies/${filename}`;
    return (
        <div className="video-container">
            <video className='responsive-video' controls>
                <source src={api} type="video/mp4" />
                Your browser does not support the video tag.
            </video>
        </div>
    );
};

export default VideoPlayer;