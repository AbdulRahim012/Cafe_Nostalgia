Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      post 'questions', to: 'questions#create'
      get 'auth/shopify', to: 'auth#shopify_oauth'
      get 'auth/shopify/callback', to: 'auth#shopify_callback'
    end
  end
end

