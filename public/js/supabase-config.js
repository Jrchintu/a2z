// Supabase Configuration
const SUPABASE_URL = 'https://bgfrokougjvzyvmehhsw.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_fSG8nDsJv4vkat_dnu8-LQ_-FLvh7Y4';
const SITE_URL = 'https://jrchintu.github.io/a2z/public/';

// Initialize Supabase client (use different variable name to avoid conflict with CDN global)
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Auth state management
const Auth = {
    currentUser: null,

    // Initialize auth state
    async init() {
        try {
            // Check for existing session
            const { data: { session }, error } = await supabaseClient.auth.getSession();
            if (error) throw error;
            
            this.currentUser = session?.user || null;
            this.updateUI();
            
            // Listen for auth state changes
            supabaseClient.auth.onAuthStateChange((event, session) => {
                this.currentUser = session?.user || null;
                this.updateUI();
                
                if (event === 'SIGNED_IN') {
                    this.syncProgressToCloud();
                }
            });
        } catch (error) {
            console.error('Auth initialization error:', error);
        }
    },

    // Sign in with email and password
    async signInWithEmail(email, password) {
        try {
            const { data, error } = await supabaseClient.auth.signInWithPassword({
                email,
                password
            });
            if (error) throw error;
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    // Sign up with email and password
    async signUpWithEmail(email, password) {
        try {
            const { data, error } = await supabaseClient.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: SITE_URL
                }
            });
            if (error) throw error;
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    // Sign in with OAuth provider (Google, GitHub)
    async signInWithProvider(provider) {
        try {
            const { data, error } = await supabaseClient.auth.signInWithOAuth({
                provider,
                options: {
                    redirectTo: SITE_URL
                }
            });
            if (error) throw error;
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    // Sign out
    async signOut() {
        try {
            const { error } = await supabaseClient.auth.signOut();
            if (error) throw error;
            this.currentUser = null;
            this.updateUI();
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    // Password reset
    async resetPassword(email) {
        try {
            const { error } = await supabaseClient.auth.resetPasswordForEmail(email, {
                redirectTo: `${SITE_URL}reset-password.html`
            });
            if (error) throw error;
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    // Update password (after reset)
    async updatePassword(newPassword) {
        try {
            const { error } = await supabaseClient.auth.updateUser({
                password: newPassword
            });
            if (error) throw error;
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    // Update UI based on auth state
    updateUI() {
        const authContainer = document.getElementById('auth-container');
        const userInfo = document.getElementById('user-info');
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const userEmail = document.getElementById('user-email');

        if (this.currentUser) {
            if (loginBtn) loginBtn.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = 'inline-flex';
            if (userInfo) userInfo.style.display = 'flex';
            if (userEmail) userEmail.textContent = this.currentUser.email;
        } else {
            if (loginBtn) loginBtn.style.display = 'inline-flex';
            if (logoutBtn) logoutBtn.style.display = 'none';
            if (userInfo) userInfo.style.display = 'none';
        }
    },

    // Sync local progress to cloud (for logged-in users)
    async syncProgressToCloud() {
        if (!this.currentUser) return;
        
        try {
            const localProgress = JSON.parse(localStorage.getItem('dsaRoadmapProgress') || '{}');
            
            // Get cloud progress
            const { data: cloudData, error: fetchError } = await supabaseClient
                .from('user_progress')
                .select('progress')
                .eq('user_id', this.currentUser.id)
                .single();
            
            if (fetchError && fetchError.code !== 'PGRST116') {
                // PGRST116 = no rows returned, which is fine for new users
                throw fetchError;
            }
            
            const cloudProgress = cloudData?.progress || {};
            
            // Merge progress (local wins for conflicts, keeping completed items)
            const mergedProgress = { ...cloudProgress };
            for (const [key, value] of Object.entries(localProgress)) {
                if (value === true) {
                    mergedProgress[key] = true;
                }
            }
            
            // Upsert to cloud
            const { error: upsertError } = await supabaseClient
                .from('user_progress')
                .upsert({
                    user_id: this.currentUser.id,
                    progress: mergedProgress,
                    updated_at: new Date().toISOString()
                }, { onConflict: 'user_id' });
            
            if (upsertError) throw upsertError;
            
            // Update local storage with merged progress
            localStorage.setItem('dsaRoadmapProgress', JSON.stringify(mergedProgress));
            
            console.log('Progress synced successfully');
        } catch (error) {
            console.error('Error syncing progress:', error);
        }
    },

    // Save progress to cloud
    async saveProgressToCloud(progress) {
        if (!this.currentUser) return;
        
        try {
            const { error } = await supabaseClient
                .from('user_progress')
                .upsert({
                    user_id: this.currentUser.id,
                    progress: progress,
                    updated_at: new Date().toISOString()
                }, { onConflict: 'user_id' });
            
            if (error) throw error;
        } catch (error) {
            console.error('Error saving progress:', error);
        }
    },

    // Load progress from cloud
    async loadProgressFromCloud() {
        if (!this.currentUser) return null;
        
        try {
            const { data, error } = await supabaseClient
                .from('user_progress')
                .select('progress')
                .eq('user_id', this.currentUser.id)
                .single();
            
            if (error && error.code !== 'PGRST116') throw error;
            return data?.progress || null;
        } catch (error) {
            console.error('Error loading progress:', error);
            return null;
        }
    }
};

// Initialize auth when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});
