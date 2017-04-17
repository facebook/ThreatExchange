class Ability
    include CanCan::Ability

    def initialize(user)
        if user
        	can :update, User, :id => user.id
        	can :show, User, :id => user.id
            can :show, IndicatorType
            can :show, ThreatType
        end
    end
end
