import React from 'react';
import { Box, BoxProps } from '@mui/material';

interface PageContainerProps extends BoxProps {
  children: React.ReactNode;
}

const PageContainer: React.FC<PageContainerProps> = ({ children, ...rest }) => {
  return (
    <Box
      sx={{
        p: 1.25, // 2px padding
        display: 'flex',
        flexDirection: 'column',
        gap: 1, // 8px gap
        ...rest.sx,
      }}
      {...rest}
    >
      {children}
    </Box>
  );
};

export default PageContainer;