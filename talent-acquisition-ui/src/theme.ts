// src/theme.ts
import { createTheme, ThemeOptions } from '@mui/material/styles';

// Consider adding a modern font like Plus Jakarta Sans (as used in the example)
// You'd typically add the @import in your main CSS file (e.g., index.css) or public/index.html
// @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#5D87FF', // A modern, friendly blue
      light: '#EBF3FE', // A very light blue for backgrounds/hovers
      dark: '#4570EA',
    },
    secondary: {
      main: '#49BEFF', // A secondary accent
    },
    background: {
      default: '#FAFBFC', // Very light grey for page background
      paper: '#FFFFFF',   // White for cards, sidebar, header
    },
    text: {
      primary: '#2A3547',   // Dark grey for primary text
      secondary: '#5A6A85', // Medium grey for secondary text
    },
    action: {
      hoverOpacity: 0.04, // Softer hover for list items etc.
      selectedOpacity: 0.08,
    },
    divider: '#EAEFF4', // Lighter divider color
  },
  typography: {
    fontFamily: '"Inter", "Plus Jakarta Sans", sans-serif', // Added Plus Jakarta Sans as primary
    h1: { fontWeight: 700, fontSize: '2.25rem', lineHeight: 1.2, color: '#2A3547' }, // 36px
    h2: { fontWeight: 700, fontSize: '2rem', lineHeight: 1.2, color: '#2A3547' },    // 32px
    h3: { fontWeight: 600, fontSize: '1.75rem', lineHeight: 1.2, color: '#2A3547' }, // 28px
    h4: { fontWeight: 600, fontSize: '1.5rem', lineHeight: 1.2, color: '#2A3547' },   // 24px
    h5: { fontWeight: 600, fontSize: '1.25rem', lineHeight: 1.2, color: '#2A3547' },  // 20px
    h6: { fontWeight: 600, fontSize: '1.125rem', lineHeight: 1.2, color: '#2A3547' },// 18px for titles
    body1: { fontSize: '1rem', color: '#2A3547' }, // 16px
    body2: { fontSize: '0.875rem', color: '#5A6A85' }, // 14px
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
    caption: { fontSize: '0.75rem', color: '#5A6A85' }, // 12px
  },
  shape: {
    borderRadius: 7, // Consistent border radius, similar to the example
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: "#A9A9A9 #F5F5F5", // For Firefox
          "&::-webkit-scrollbar, & *::-webkit-scrollbar": {
            backgroundColor: "#F5F5F5",
            width: '8px',
            height: '8px',
          },
          "&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb": {
            borderRadius: 8,
            backgroundColor: "#A9A9A9",
            minHeight: 24,
            border: "2px solid #F5F5F5",
          },
          "&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus": {
            backgroundColor: "#7D7D7D",
          },
          "&::-webkit-scrollbar-thumb:active, & *::-webkit-scrollbar-thumb:active": {
            backgroundColor: "#7D7D7D",
          },
          "&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover": {
            backgroundColor: "#7D7D7D",
          },
        },
      },
    },
    MuiAppBar: {
      defaultProps: {
        elevation: 0, // Flat header
        color: 'inherit', // To use background.paper or a custom color
      },
      styleOverrides: {
        root: ({ theme }) => ({
          backgroundColor: theme.palette.background.paper, // White header
          borderBottom: `1px solid ${theme.palette.divider}`, // Subtle bottom border
          color: theme.palette.text.primary,
        }),
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: ({ theme }) => ({
          backgroundColor: theme.palette.background.paper, // White sidebar
          borderRight: 'none', // No border for a cleaner look if combined with main content bg
          // width: drawerWidth (will be handled in component)
        }),
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 0, // Default to no elevation, add where needed for emphasis
      },
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: theme.shape.borderRadius,
          boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.05)', // Softer, more modern shadow
          // border: `1px solid ${theme.palette.divider}`, // Alternative to shadow
        }),
      },
    },
    MuiButton: {
      defaultProps: {
        size: 'small',
      },
      styleOverrides: {
        root: {
          borderRadius: '7px', // Match global borderRadius
          padding: '8px 16px',
        },
        containedPrimary: ({ theme }) => ({
          boxShadow: `0 4px 8px -4px ${theme.palette.primary.main}`,
          '&:hover': {
            boxShadow: `0 6px 12px -4px ${theme.palette.primary.main}`,
          },
        }),
        containedSecondary: ({ theme }) => ({
           boxShadow: `0 4px 8px -4px ${theme.palette.secondary.main}`,
           '&:hover': {
            boxShadow: `0 6px 12px -4px ${theme.palette.secondary.main}`,
          },
        })
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: theme.shape.borderRadius,
          margin: theme.spacing(0.25, 0.75), // Even tighter horizontal margin (6px)
          paddingLeft: theme.spacing(1.25),    // Further reduced horizontal padding (10px)
          paddingRight: theme.spacing(1.25),   // Further reduced horizontal padding (10px)
          '&:hover': {
            backgroundColor: theme.palette.primary.light, // Use light primary for hover
            color: theme.palette.primary.main,
             '& .MuiListItemIcon-root': {
                color: theme.palette.primary.main,
            },
          },
          '&.Mui-selected': {
            backgroundColor: theme.palette.primary.main,
            color: theme.palette.primary.contrastText, // White text on primary background
            '& .MuiListItemIcon-root': {
              color: theme.palette.primary.contrastText,
            },
            '&:hover': {
              backgroundColor: theme.palette.primary.dark, // Darken on hover when selected
            }
          },
        }),
      },
    },
    MuiOutlinedInput: {
        styleOverrides: {
            root: ({theme}) => ({
                borderRadius: theme.shape.borderRadius,
                 '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: theme.palette.primary.light,
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: theme.palette.primary.main,
                    borderWidth: '1px', // Ensure focus ring is not too thick
                },
            }),
            notchedOutline: ({theme}) => ({
                borderColor: theme.palette.divider, // Lighter default border
            })
        }
    },
    MuiInputLabel: {
        styleOverrides: {
            root: ({theme}) => ({
                color: theme.palette.text.secondary,
            })
        }
    },
    MuiFormControl: {
      defaultProps: {
        size: 'small',
      },
    },
    MuiChip: {
      defaultProps: {
        size: 'small',
      },
    },
    MuiTextField: {
      defaultProps: {
        size: 'small',
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: ({ theme }) => ({
          boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.05)', // Use consistent shadow from Card
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: theme.shape.borderRadius,
        }),
      },
    },
    MuiTooltip: {
        styleOverrides: {
            tooltip: ({theme}) => ({
                backgroundColor: theme.palette.grey[700],
                borderRadius: theme.shape.borderRadius,
            }),
            arrow: ({theme}) => ({
                color: theme.palette.grey[700],
            })
        }
    }
  },
};

const theme = createTheme(themeOptions);

export default theme;