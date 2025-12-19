require_relative "boot"

require "rails/all"

Bundler.require(*Rails.groups)

module ShopifyAnalyticsApi
  class Application < Rails::Application
    config.load_defaults 7.1
    config.api_only = true
    
    config.middleware.use Rack::Cors do
      allow do
        origins '*'
        resource '*',
          headers: :any,
          methods: [:get, :post, :put, :patch, :delete, :options, :head]
      end
    end
  end
end

