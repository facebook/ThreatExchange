class AddAppCredentialsToUsers < ActiveRecord::Migration
  def change
    add_column :users, :app_id, :string
    add_index :users, :app_id
    add_column :users, :app_secret, :string
    add_index :users, :app_secret
  end
end
