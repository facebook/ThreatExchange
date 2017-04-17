Rails.application.routes.draw do
    # root 'welcome#index'

    get "home" => "welcome#index", :as => "home"
    get "result", to: "threats#result"
    post "submit", to: "threats#submit"
    get "profile" => "users#edit", :as => "profile"

    # Welcome Controller
    %w[terms about].each do |page|
        get page, controller: "welcome", action: page
    end

    # Devise
    devise_for :users, :controllers => { registrations: "users/registrations", sessions: "users/sessions" }
    devise_scope :user do
        root 'devise/sessions#new'
    end

    # Resources
    resources :threats, :only => [:new, :create, :show], constraints: { id: /[0-z\.\-\/\@\%\+\;]+/ }
    resources :users, :only => [:edit, :show, :update]
end
