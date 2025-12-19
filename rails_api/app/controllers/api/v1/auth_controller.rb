module Api
  module V1
    class AuthController < ApplicationController
      def shopify_oauth
        shop = params[:shop]
        redirect_uri = "#{request.base_url}/api/v1/auth/shopify/callback"
        
        auth_url = ShopifyOAuthService.new.authorize_url(
          shop: shop,
          redirect_uri: redirect_uri
        )
        
        redirect_to auth_url, allow_other_host: true
      end

      def shopify_callback
        code = params[:code]
        shop = params[:shop]
        
        token_response = ShopifyOAuthService.new.get_access_token(
          shop: shop,
          code: code
        )
        
        if token_response[:success]
          # Store the access token (in production, save to database)
          render json: {
            message: 'Authentication successful',
            shop: shop,
            access_token: token_response[:access_token]
          }, status: :ok
        else
          render json: {
            error: 'Authentication failed',
            details: token_response[:error]
          }, status: :unprocessable_entity
        end
      end
    end
  end
end

