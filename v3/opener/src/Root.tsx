import React from 'react';
import {Composition} from 'remotion';
import {Opener, OpenerProps} from './Opener';

const FPS = 30;

export const Root: React.FC = () => (
  <Composition
    id="Opener"
    component={Opener}
    fps={FPS}
    width={1920}
    height={1080}
    durationInFrames={FPS * 20}
    defaultProps={{duration: 20, words: [], beats: [], show: 'Tech-dev', badge: '', look: 'mission'} as OpenerProps}
    calculateMetadata={({props}) => ({durationInFrames: Math.ceil((props as OpenerProps).duration * FPS)})}
  />
);
