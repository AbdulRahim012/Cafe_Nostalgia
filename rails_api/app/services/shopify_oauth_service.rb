class ShopifyOAuthService
  include HTTParty
  
  def initialize
    @api_key = ENV['SHOPIFY_API_KEY']
    @api_secret = ENV['SHOPIFY_API_SECRET']
    @scopes = 'read_orders,read_products,read_inventory'
  end

  def authorize_url(shop:, redirect_uri:)
    shop = normalize_shop(shop)
    "https://#{shop}/admin/oauth/authorize?client_id=#{@api_key}&scope=#{@scopes}&redirect_uri=#{CGI.escape(redirect_uri)}"
  end

  def get_access_token(shop:, code:)
    shop = normalize_shop(shop)
    
    response = HTTParty.post("https://#{shop}/admin/oauth/access_token", {
      body: {
        client_id: @api_key,
        client_secret: @api_secret,
        code: code
      }.to_json,
      headers: {
        'Content-Type' => 'application/json'
      }
    })
    
    if response.success? && response['access_token']
      {
        success: true,
        access_token: response['access_token']
      }
    else
      {
        success: false,
        error: response['error'] || 'Failed to get access token'
      }
    end
  rescue => e
    {
      success: false,
      error: e.message
    }
  end

  private

  def normalize_shop(shop)
    shop = shop.gsub(/^https?:\/\//, '')
    shop = shop.gsub(/\.myshopify\.com.*$/, '')
    "#{shop}.myshopify.com"
  end
end

