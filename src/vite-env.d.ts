/// <reference types="vite/client" />

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (options: {
            client_id: string;
            callback: (response: { credential?: string }) => void;
            auto_select?: boolean;
            cancel_on_tap_outside?: boolean;
          }) => void;
          renderButton: (
            element: HTMLElement,
            options: {
              theme?: 'outline' | 'filled_blue' | 'filled_black';
              size?: 'large' | 'medium' | 'small';
              type?: 'standard' | 'icon';
              text?: string;
              shape?: 'rectangular' | 'pill';
              logo_alignment?: 'left' | 'center';
            }
          ) => void;
          prompt: (callback?: () => void) => void;
        };
      };
    };
  }
}

export {};
