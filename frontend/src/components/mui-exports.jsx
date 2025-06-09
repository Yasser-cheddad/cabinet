// This file exports Material-UI components from the global CDN-loaded version
// to be used as regular imports in our components

// Check if we're in the browser environment
const isBrowser = typeof window !== 'undefined';

// Get the Material-UI components from the global object
const MaterialUI = isBrowser ? window.MaterialUI : {};
const MaterialUIIcons = isBrowser ? window.MaterialUIIcons : {};

// Export individual components
export const Box = MaterialUI?.Box;
export const Card = MaterialUI?.Card;
export const CardContent = MaterialUI?.CardContent;
export const Typography = MaterialUI?.Typography;
export const Button = MaterialUI?.Button;
export const Grid = MaterialUI?.Grid;
export const Tabs = MaterialUI?.Tabs;
export const Tab = MaterialUI?.Tab;
export const CircularProgress = MaterialUI?.CircularProgress;
export const TextField = MaterialUI?.TextField;
export const Dialog = MaterialUI?.Dialog;
export const DialogTitle = MaterialUI?.DialogTitle;
export const DialogContent = MaterialUI?.DialogContent;
export const DialogActions = MaterialUI?.DialogActions;
export const IconButton = MaterialUI?.IconButton;
export const Table = MaterialUI?.Table;
export const TableBody = MaterialUI?.TableBody;
export const TableCell = MaterialUI?.TableCell;
export const TableContainer = MaterialUI?.TableContainer;
export const TableHead = MaterialUI?.TableHead;
export const TableRow = MaterialUI?.TableRow;
export const Paper = MaterialUI?.Paper;
export const Divider = MaterialUI?.Divider;
export const List = MaterialUI?.List;
export const ListItem = MaterialUI?.ListItem;
export const ListItemText = MaterialUI?.ListItemText;
export const ListItemIcon = MaterialUI?.ListItemIcon;
export const FormControl = MaterialUI?.FormControl;
export const InputLabel = MaterialUI?.InputLabel;
export const Select = MaterialUI?.Select;
export const MenuItem = MaterialUI?.MenuItem;
export const Snackbar = MaterialUI?.Snackbar;
export const Alert = MaterialUI?.Alert;
export const Tooltip = MaterialUI?.Tooltip;
export const Container = MaterialUI?.Container;
export const AppBar = MaterialUI?.AppBar;
export const Toolbar = MaterialUI?.Toolbar;
export const Drawer = MaterialUI?.Drawer;
export const Menu = MaterialUI?.Menu;
export const Avatar = MaterialUI?.Avatar;
export const Chip = MaterialUI?.Chip;
export const Badge = MaterialUI?.Badge;
export const Checkbox = MaterialUI?.Checkbox;
export const Radio = MaterialUI?.Radio;
export const RadioGroup = MaterialUI?.RadioGroup;
export const FormControlLabel = MaterialUI?.FormControlLabel;
export const FormGroup = MaterialUI?.FormGroup;
export const Switch = MaterialUI?.Switch;

// Icons
export const AddIcon = MaterialUIIcons?.Add;
export const EditIcon = MaterialUIIcons?.Edit;
export const DeleteIcon = MaterialUIIcons?.Delete;
export const CloudUploadIcon = MaterialUIIcons?.CloudUpload;
export const CloudDownloadIcon = MaterialUIIcons?.CloudDownload;
export const CloseIcon = MaterialUIIcons?.Close;
export const MenuIcon = MaterialUIIcons?.Menu;
export const SearchIcon = MaterialUIIcons?.Search;
export const MoreVertIcon = MaterialUIIcons?.MoreVert;
export const PersonIcon = MaterialUIIcons?.Person;
export const CalendarTodayIcon = MaterialUIIcons?.CalendarToday;
export const EventIcon = MaterialUIIcons?.Event;
export const NoteIcon = MaterialUIIcons?.Note;
export const FolderIcon = MaterialUIIcons?.Folder;
export const HomeIcon = MaterialUIIcons?.Home;
export const SettingsIcon = MaterialUIIcons?.Settings;
export const LogoutIcon = MaterialUIIcons?.Logout;
export const LoginIcon = MaterialUIIcons?.Login;
export const DashboardIcon = MaterialUIIcons?.Dashboard;
export const PeopleIcon = MaterialUIIcons?.People;
export const LocalHospitalIcon = MaterialUIIcons?.LocalHospital;
export const AccessTimeIcon = MaterialUIIcons?.AccessTime;
export const PrintIcon = MaterialUIIcons?.Print;
export const AttachFileIcon = MaterialUIIcons?.AttachFile;
export const DescriptionIcon = MaterialUIIcons?.Description;
export const NotificationsIcon = MaterialUIIcons?.Notifications;
export const ExpandMoreIcon = MaterialUIIcons?.ExpandMore;
export const ChevronLeftIcon = MaterialUIIcons?.ChevronLeft;
export const ChevronRightIcon = MaterialUIIcons?.ChevronRight;

// Styles
export const useTheme = MaterialUI?.styles?.useTheme;
export const styled = MaterialUI?.styles?.styled;

// Export default for compatibility
export default {
  Box, Card, CardContent, Typography, Button, Grid, Tabs, Tab, CircularProgress,
  TextField, Dialog, DialogTitle, DialogContent, DialogActions, IconButton,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Divider, List, ListItem, ListItemText, ListItemIcon, FormControl, InputLabel,
  Select, MenuItem, Snackbar, Alert, Tooltip, Container, AppBar, Toolbar,
  Drawer, Menu, Avatar, Chip, Badge, Checkbox, Radio, RadioGroup, FormControlLabel,
  FormGroup, Switch,
  
  // Icons
  AddIcon, EditIcon, DeleteIcon, CloudUploadIcon, CloudDownloadIcon, CloseIcon,
  MenuIcon, SearchIcon, MoreVertIcon, PersonIcon, CalendarTodayIcon, EventIcon,
  NoteIcon, FolderIcon, HomeIcon, SettingsIcon, LogoutIcon, LoginIcon, DashboardIcon,
  PeopleIcon, LocalHospitalIcon, AccessTimeIcon, PrintIcon, AttachFileIcon,
  DescriptionIcon, NotificationsIcon, ExpandMoreIcon, ChevronLeftIcon, ChevronRightIcon,
  
  // Styles
  useTheme, styled
};
