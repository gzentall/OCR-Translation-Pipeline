/**
 * Shared Header Component JavaScript
 * Handles profile menu, user authentication, and header interactions
 */

class HeaderService {
    constructor() {
        this.user = null;
        this.isMenuOpen = false;
        this.init();
    }

    init() {
        this.loadUserInfo();
        this.setupEventListeners();
        this.initializeUserAvatar();
    }

    loadUserInfo() {
        // Get user info from page data or localStorage
        if (window.userInfo) {
            this.user = window.userInfo;
        } else {
            // Fallback to localStorage
            const userEmail = localStorage.getItem('userEmail') || 'User';
            const userName = localStorage.getItem('userName') || 'User';
            const userRole = localStorage.getItem('userRole') || 'viewer';
            
            this.user = {
                name: userName,
                email: userEmail,
                role: userRole,
                initials: this.getUserInitials(userName)
            };
        }
    }

    getUserInitials(name) {
        if (!name || name === 'User') return 'U';
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }

    getRoleDisplayName(role) {
        const roleMap = {
            'admin': 'Super Admin',
            'viewer': 'Viewer',
            'editor': 'Editor'
        };
        return roleMap[role] || 'Viewer';
    }

    initializeUserAvatar() {
        const avatar = document.getElementById('userAvatar');
        const profileAvatar = document.getElementById('profileAvatar');
        const profileName = document.getElementById('profileName');
        const profileRole = document.getElementById('profileRole');

        if (avatar && this.user) {
            avatar.textContent = this.user.initials;
        }
        
        if (profileAvatar && this.user) {
            profileAvatar.textContent = this.user.initials;
        }
        
        if (profileName && this.user) {
            profileName.textContent = this.user.name;
        }
        
        if (profileRole && this.user) {
            profileRole.textContent = this.getRoleDisplayName(this.user.role);
        }
    }

    setupEventListeners() {
        // Close menu on outside click
        document.addEventListener('click', (event) => {
            const dropdown = document.getElementById('profileDropdown');
            const avatarButton = document.querySelector('.avatar-button');
            
            if (dropdown && avatarButton && 
                !dropdown.contains(event.target) && 
                !avatarButton.contains(event.target)) {
                this.closeProfileMenu();
            }
        });

        // Reposition menu on resize
        window.addEventListener('resize', () => {
            if (this.isMenuOpen) {
                this.positionMenu();
            }
        });
    }

    toggleProfileMenu() {
        const dropdown = document.getElementById('profileDropdown');
        const avatarButton = document.querySelector('.avatar-button');
        
        if (!dropdown || !avatarButton) {
            console.error('Header elements not found');
            return;
        }

        this.isMenuOpen = !this.isMenuOpen;

        if (this.isMenuOpen) {
            this.openProfileMenu();
        } else {
            this.closeProfileMenu();
        }
    }

    openProfileMenu() {
        const dropdown = document.getElementById('profileDropdown');
        const avatarButton = document.querySelector('.avatar-button');
        
        dropdown.classList.add('is-open');
        this.positionMenu(dropdown, avatarButton);
        this.isMenuOpen = true;
    }

    closeProfileMenu() {
        const dropdown = document.getElementById('profileDropdown');
        if (dropdown) {
            dropdown.classList.remove('is-open');
            this.isMenuOpen = false;
        }
    }

    positionMenu(menu, trigger) {
        const MENU_WIDTH = 280;
        const GAP = 8;
        
        const triggerRect = trigger.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Calculate position: align menu's right edge with trigger's right edge
        let left = triggerRect.right - MENU_WIDTH;
        let top = triggerRect.bottom + GAP;
        
        // Clamp to viewport
        if (left < GAP) {
            left = GAP;
        }
        if (left + MENU_WIDTH > viewportWidth - GAP) {
            left = viewportWidth - MENU_WIDTH - GAP;
        }
        
        if (top + 200 > viewportHeight - GAP) {
            top = Math.max(GAP, viewportHeight - 200 - GAP);
        }
        
        // Apply positioning
        menu.style.left = `${left}px`;
        menu.style.top = `${top}px`;
        menu.style.right = 'auto';
        menu.style.bottom = 'auto';
    }

    logout() {
        // Clear authentication data
        localStorage.clear();
        sessionStorage.clear();
        
        // Redirect to login
        window.location.href = '/login';
    }

    showUploadModal() {
        // This would be implemented by the specific page
        console.log('Upload modal requested');
    }
}

// Initialize header service when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.headerService = new HeaderService();
    
    // Make functions globally available for onclick handlers
    window.toggleProfileMenu = () => window.headerService.toggleProfileMenu();
    window.logout = () => window.headerService.logout();
    window.showUploadModal = () => window.headerService.showUploadModal();
});
