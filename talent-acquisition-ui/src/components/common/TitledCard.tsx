import React from 'react';
import { Card, CardHeader, CardContent, Divider, CardProps } from '@mui/material';

// Use Omit to prevent conflict with the standard HTML 'title' attribute from CardProps
interface TitledCardProps extends Omit<CardProps, 'title'> {
  title: React.ReactNode;
  children: React.ReactNode;
  disableContentPadding?: boolean;
}

const TitledCard: React.FC<TitledCardProps> = ({ title, children, disableContentPadding = false, elevation = 2, ...rest }) => {
  return (
    <Card elevation={elevation} {...rest}>
      <CardHeader
        title={title}
        titleTypographyProps={{ variant: 'h6', sx: { fontSize: '1.1rem' } }}
        sx={{ py: 1, px: 1.5, bgcolor: 'action.hover' }}
      />
      <Divider />
      <CardContent sx={{ p: disableContentPadding ? 0 : 1.5 }}>
        {children}
      </CardContent>
    </Card>
  );
};

export default TitledCard;